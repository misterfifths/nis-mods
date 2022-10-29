import ctypes as C
import math
import struct
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Annotated, Iterator, Sequence, Union

from astruct import typed_struct
from astruct.type_hints import *
from utils import hexdump, private_mmap
from utils.hexdump.byte_utils import hexlify

# Massive debt to ChepChep, who was responsible for the English port of Makai
# Kingdom Portable, for figuring out the details of this compression scheme.
# See this post in particular:
# https://gbatemp.net/threads/phantom-kingdom-portable-english-translation.365313/#post-4981369


@typed_struct
class YKCMPHeader(C.Structure):
    MAGIC = 'YKCMP_V1'
    UNKNOWN_FIELD_VALUE = 4

    _pack_ = 1

    magic: Annotated[CStr[8], NotNullTerminated()]
    _unk: CUInt32
    compressed_size: CUInt32
    decompressed_size: CUInt32

    def validate(self) -> None:
        if self.magic != YKCMPHeader.MAGIC:
            raise ValueError(f'Invalid magic in YKCMP header: {self.magic!r}')

        # Not actually sure if this is important, but checking it can't hurt.
        if self._unk != YKCMPHeader.UNKNOWN_FIELD_VALUE:
            raise ValueError(f'Invalid constant in YKCMP header: {self._unk}')


class YKCMPArchive:
    _buffer: WriteableBuffer
    _header: YKCMPHeader

    _base_offset: int
    _data_start: int
    _data_end: int

    def __init__(self, buffer: WriteableBuffer, offset: int = 0) -> None:
        self._buffer = buffer
        self._base_offset = offset

        self._header = YKCMPHeader.from_buffer(buffer, offset)  # type: ignore[arg-type]
        self._header.validate()

        self._data_start = offset + C.sizeof(YKCMPHeader)
        self._data_end = offset + self._header.compressed_size

        if self._data_end > len(self._buffer):
            raise IndexError('Archive says its compressed data extends past end of buffer: '
                             f'offset {offset:x} and compressed size '
                             f'{self._header.compressed_size:x} puts end of data at byte '
                             f'{self._data_end:x}, but buffer is only {len(self._buffer):x} '
                             'bytes long')

    @classmethod
    @contextmanager
    def from_file(cls, path: Union[Path, str]) -> Iterator['YKCMPArchive']:
        with private_mmap(path) as mm:
            yield cls(mm)

    def _read_byte(self, p: int) -> int:
        """Read one byte from the input buffer at index p.

        Raises a helpful IndexError on bounds issues.
        """
        if p < self._data_start or p >= self._data_end:
            raise IndexError(f'Out of range read during decompression: {p:x} not in '
                             f'{self._data_start:x} - {self._data_end:x}')

        return self._buffer[p]

    def _read_and_output(self, ip: int, n: int, output: WriteableBuffer, op: int) -> None:
        """Copy n bytes from the input buffer starting at index ip to the
        output buffer starting at index op.

        Bounds errors will raise IndexError.
        """
        if ip < self._data_start or ip + n > self._data_end:
            raise IndexError(f'Out of range read during decompression: {ip:x} - {ip + n:x} not in '
                             f'{self._data_start:x} - {self._data_end:x}')

        if n < 0:
            raise IndexError(f'Negative-length read during decompression: {n} at {ip:x}')

        if op < 0:
            raise IndexError(f'Negative output index during decompression: {op:x} at input {ip:x}')

        # This is important for sanity, but also to make sure we don't
        # accidentally extend the output buffer via slice syntax.
        if op + n > len(output):
            raise IndexError('Decompression would exceed bounds of output')

        output[op:op + n] = self._buffer[ip:ip + n]

    def _repeat_output(self, output: WriteableBuffer, p: int, n: int, op: int) -> None:
        """Copy n bytes from the given output buffer starting at index p to
        itself, starting at index op.

        Bounds errors will raise IndexError.
        """
        if p < 0:
            raise IndexError(f'Negative index into output during decompression: {p:x}')

        if n < 0:
            raise IndexError(f'Negative-length read during decompression: {n} at {p:x}')

        if op < 0:
            raise IndexError(f'Negative output index during decompression: {op:x}')

        if op + n > len(output) or p + n > len(output):
            raise IndexError('Decompression would exceed bounds of output')

        if p + n > op:
            # Not sure if this is technically allowed, but it's been indicative
            # of errors every time I've seen it.
            raise IndexError(f'Decompression reading uninitialized bytes in output: {p + n:x} is '
                             f'past the output at {op:x}')

        output[op:op + n] = output[p:p + n]

    def _debug_hexdump(self, buffer: WriteableBuffer, offset: int) -> None:
        """Prints a hexdump to stderr ending at the given offset in buffer,
        with some context preceding it.

        The dump is aligned to begin at a multiple of 16 bytes.
        """
        MAX_BYTES = 128
        ctx_offset = max(0, (offset - MAX_BYTES) & ~0xf)
        ctx_count = offset - ctx_offset
        hexdump(buffer,
                offset=ctx_offset,
                count=ctx_count,
                encoding='shift-jis',
                file=sys.stderr)
        print(file=sys.stderr)

    def decompress(self, debug: bool = False) -> bytearray:
        """Decompress the input buffer and return the resulting bytes."""
        res = bytearray(self._header.decompressed_size)

        ip = self._data_start
        op = 0

        while ip < self._data_end:
            b1 = self._read_byte(ip)

            # A zero byte is an absolute lookbehind in the output. It's a
            # seven-byte instruction: 00 AA AA AA AA BB BB.
            # The A bytes form an unsigned 32-bit offset from the start of the
            # output buffer. The B bytes form an unsigned 16-bit count.
            # We are to go back to the offset in the output formed by the A
            # bytes, and copy count many bytes from there to the end.
            if b1 == 0:
                bs = bytes(self._read_byte(ip + i + 1) for i in range(6))
                offset, count = struct.unpack('<IH', bs)

                if debug:
                    print(f'@{ip:08x} {b1:02x} {hexlify(bs)}: absolute copy {count:x} bytes from '
                          f'{offset:x}', file=sys.stderr)

                self._repeat_output(res, offset, count, op)

                if debug:
                    self._debug_hexdump(res, op)

                op += count
                ip += 7

                continue

            # Nonzero values less than 0x80 mean "copy that many bytes from the
            # input straight to the output"
            if b1 < 0x80:
                if debug:
                    print(f'@{ip:08x} {b1:02x}: verbatim {b1:x} bytes', file=sys.stderr)

                ip += 1
                self._read_and_output(ip, b1, res, op)
                ip += b1
                op += b1

                if debug:
                    self._debug_hexdump(res, op)

                continue

            # Other values are relative lookbacks that all mean "go back a
            # certain number of bytes *in the output* and copy a certain other
            # number of bytes from there to the end of output."
            # How far we go back and how many bytes we copy are based on a
            # calculation involving the input byte, and up to two bytes after
            # it.
            # We break the bits of the 1-3 bytes into two numbers, X and Y,
            # described in each case below. Then there's a base we subtract
            # from X that depends on how many bytes we read.
            # When all is said and done, we go back *in the output* Y + 1
            # bytes, and copy the following X - base + {1, 2, or 3} bytes to
            # the end.
            if b1 < 0xc0:
                # One-byte lookback. The base is 0x08.
                # The byte breaks down into XY
                # ex: 9f ==> X = 9, Y = f
                x_base = 0x08

                x = (b1 & 0xf0) >> 4
                y = b1 & 0x0f

                advance = 1
            elif b1 < 0xe0:
                # Two-byte lookback. The base is 0xc0.
                # This byte and the one after it are XXYY
                # ex: c5 11 ==> X = c5, Y = 11
                x_base = 0xc0

                x = b1
                y = self._read_byte(ip + 1)

                advance = 2
            else:
                # Three-byte lookback. The base is 0x0e00.
                # This byte and two after it are XXXYYY
                # ex: 1f f3 fe ==> x = 1ff, y = 3fe
                x_base = 0x0e00

                b2 = self._read_byte(ip + 1)
                b3 = self._read_byte(ip + 2)

                x = (b1 << 4) | ((b2 & 0xf0) >> 4)
                y = ((b2 & 0x0f) << 8) | b3

                advance = 3

            move_back = y + 1
            read_len = x - x_base + advance

            if debug:
                bs = bytes(self._read_byte(ip + i) for i in range(advance))
                print(f'@{ip:08x} {hexlify(bs)}: dup {read_len:x} bytes from -{move_back:x}, '
                      f'advance {advance}', file=sys.stderr)

            self._repeat_output(res, op - move_back, read_len, op)
            op += read_len
            ip += advance

            if debug:
                self._debug_hexdump(res, op)

        return res

    @classmethod
    def compress(cls, data: Sequence[int]) -> 'YKCMPArchive':
        """Naively 'compress' the given data and return a new YKCMPArchive
        from the result."""
        # Most naive possible algorithm. Actually makes the "compressed" data
        # bigger, due to overhead.
        # We're going to add a simple copy instruction every 0x7f bytes (as
        # that's the maximum we can represent with that instruction)
        compressed_size = len(data) + C.sizeof(YKCMPHeader) + math.ceil(len(data) / 0x7f)

        res = bytearray(compressed_size)

        header = YKCMPHeader.from_buffer(res, 0)
        header.magic = YKCMPHeader.MAGIC
        header._unk = YKCMPHeader.UNKNOWN_FIELD  # type: ignore
        header.decompressed_size = len(data)
        header.compressed_size = compressed_size
        header.validate()

        ip = 0
        op = C.sizeof(YKCMPHeader)

        while ip < len(data):
            if ip % 0x7f == 0:
                # Output a copy instruction for either 0x7f bytes or however
                # many are left, whichever is smaller.
                res[op] = min(0x7f, len(data) - ip)
                op = op + 1

            # TODO: do this with slice syntax
            res[op] = data[ip]
            ip += 1
            op += 1

        return cls(res)

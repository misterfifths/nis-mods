import ctypes as C
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Union

from astruct import typed_struct
from astruct.type_hints import *
from utils import hexdump, private_mmap

# Thanks yet again to xdanieldzd's Scarlet project for serving as a reference
# to this format. See in particular
# https://github.com/xdanieldzd/Scarlet/blob/master/Scarlet.IO.CompressionFormats/NISLZS.cs


@typed_struct
class LZSHeader(C.Structure):
    _pack_ = 1

    file_extension: CStr[4]
    decompressed_size: CUInt32
    compressed_size: CUInt32
    flag_byte: CUInt8
    _unk: CUInt8Array[3]  # zero?


class LZSArchive:
    _buffer: WriteableBuffer
    _header: LZSHeader

    _base_offset: int
    _data_start: int
    _data_end: int

    def __init__(self, buffer: WriteableBuffer, offset: int = 0) -> None:
        self._buffer = buffer
        self._base_offset = offset

        self._header = LZSHeader.from_buffer(buffer, offset)  # type: ignore[arg-type]

        self._data_start = offset + C.sizeof(LZSHeader)

        # compressed_size seems to measure from the end of the original file
        # extension, which is 4 bytes long.
        self._data_end = offset + 4 + self._header.compressed_size

        if self._data_end > len(self._buffer):
            raise IndexError('Archive says its compressed data extends past end of buffer: '
                             f'offset {offset:x} and compressed size '
                             f'{self._header.compressed_size:x} puts end of data at byte '
                             f'{self._data_end:x}, but buffer is only {len(self._buffer):x} '
                             'bytes long')

    @classmethod
    @contextmanager
    def from_file(cls, path: Union[Path, str]) -> Iterator['LZSArchive']:
        with private_mmap(path) as mm:
            yield cls(mm)

    @property
    def original_file_extension(self) -> str:
        return self._header.file_extension

    def _read_byte(self, p: int) -> int:
        """Read one byte from the input buffer at index p.

        Raises a helpful IndexError on bounds issues.
        """
        if p < self._data_start or p >= self._data_end:
            raise IndexError(f'Out of range read during decompression: {p:x} not in '
                             f'{self._data_start:x} - {self._data_end:x}')

        return self._buffer[p]

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
        flag_byte = self._header.flag_byte
        res = bytearray(self._header.decompressed_size)

        ip = self._data_start
        op = 0

        while ip < self._data_end:
            b1 = self._read_byte(ip)
            ip += 1

            if b1 != flag_byte:
                # Verbatim output byte
                res[op] = b1
                op += 1

                # if debug:
                #     print(f'@{ip - 1:08x} {b1:02x}: verbatim {b1:02x}',
                #           file=sys.stderr)
                #     self._debug_hexdump(res, op)

                continue

            b2 = self._read_byte(ip)
            ip += 1

            if b2 == flag_byte:
                # An 'escaped' flag byte
                res[op] = b2
                op += 1

                if debug:
                    print(f'@{ip - 2:08x} {b1:02x} {b2:02x}: escaped flag {b2:02x}',
                          file=sys.stderr)
                    self._debug_hexdump(res, op)
            else:
                # Lookbehind in the decompressed data.
                # Distance back is b2 (possibly minus one), number of bytes to
                # copy is the next byte.
                move_back = b2
                if move_back > flag_byte:
                    move_back -= 1

                read_len = self._read_byte(ip)
                ip += 1

                if debug:
                    print(f'@{ip - 3:08x} {b1:02x} {b2:02x} {read_len:02x}: dup {read_len} bytes '
                          f'from -{move_back}', file=sys.stderr)

                self._repeat_output(res, op - move_back, read_len, op)
                op += read_len

                if debug:
                    self._debug_hexdump(res, op)

        return res

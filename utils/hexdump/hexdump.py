#!/usr/bin/env python3

from typing import ByteString, Optional
import math
from .decoder import iffy_decode
from .display_utils import safe_2_cell_str


def hexdump(bs: ByteString, *,
            offset: int = 0,
            count: Optional[int] = None,
            encoding: str = 'utf8',
            fallback_encoding: str = 'mac_roman',
            decimal: bool = False,
            bytes_per_line: int = 16,
            show_chars: bool = True,
            debug: bool = False) -> None:
    """Prints the given bytes in hexadecimal format, side-by-side with an
    interpretation of the bytes in the given encoding.

    hexdump attempts to recognize multibyte characters in the encoding and
    display them as well, using '⋯' to represent continuation bytes in the
    string output. Bytes that cannot be interpreted by encoding are fed
    byte-by-byte to fallback_encoding, which should be non-multibyte. If
    fallback_encoding also fails to recognize the byte, a '.' is printed in the
    output.

    Arguments:
    bs: The bytes to print.
    offset: The index of the first byte to consider in bs. Default: 0
    count: How many bytes to consider, starting at offset, or None to proceed
        to the end of bs. Default: None
    encoding: The encoding to use to generate the string interpretation on the
        right side of the output. Multibyte encodings are supported. Default:
        'utf8'
    fallback_encoding: The encoding to use in the case the initial encoding
        fails to recognize a character. Should be non-multibyte. Default:
        'mac_roman' (it has a character representation for more upper ASCII
        bytes than, say, latin-1)
    decimal: True to print in decimal rather than hexadecimal. Default: False.
    bytes_per_line: How many bytes to print per line. Default: 16
    show_chars: True to show the string interpetation of bytes on the right
        side of the output. Default: True
    debug: Show verbose information about every byte range in the input.
        Default: False
    """
    if count is None:
        count = len(bs) - offset
    else:
        count = min(len(bs) - offset, count)

    # How many hex bytes do we need to display the max address?
    addr_len = math.ceil(math.log(offset + count, 16))
    addr_len += addr_len & 1  # round to even

    byte_format = '03' if decimal else '02x'
    byte_width = 3 if decimal else 2

    decoded_byte_strs = None
    if show_chars:
        decoded_byte_strs = iffy_decode(bs, offset=offset, count=count,
                                        encoding=encoding,
                                        fallback_encoding=fallback_encoding,
                                        debug=debug)

        assert len(decoded_byte_strs) == count

    for start_addr in range(offset, offset + count, bytes_per_line):
        print(f'{start_addr:0{addr_len}x} |  ', end='')

        # The data might end before the full length of the line
        line_end_addr = min(offset + count, start_addr + bytes_per_line)

        # Calculate extra space needed before the char dump for alignment, in
        # case this isn't a full line
        bytes_on_this_line = line_end_addr - start_addr
        extra_space_before_strs = (byte_width + 1) * (bytes_per_line - bytes_on_this_line)
        if bytes_on_this_line < bytes_per_line // 2:
            # One extra if we didn't make it to the column in the center
            extra_space_before_strs += 1

        for addr in range(start_addr, line_end_addr):
            print(f'{bs[addr]:{byte_format}} ', end='')

            # Space for a column down the middle:
            if addr == (start_addr + bytes_per_line // 2) - 1:
                print(' ', end='')

        if decoded_byte_strs:
            print((extra_space_before_strs * ' ') + ' |', end='')
            for addr in range(start_addr, line_end_addr):
                # decoded_byte_strs starts has index 0 corresponding to offset
                print(safe_2_cell_str(decoded_byte_strs[addr - offset]), end='')

            print('|', end='')

        print()

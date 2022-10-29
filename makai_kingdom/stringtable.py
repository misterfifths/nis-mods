import struct
from typing import Final

from astruct.str_utils import decode_null_terminated, get_incremental_decoder
from astruct.type_hints import *


class StringTable:
    STANDARD_FILENAME: Final = 'stringtabledata.dat'

    strings: list[str]

    def __init__(self, buffer: WriteableBuffer, offset: int = 0) -> None:
        OFFSET_ENTRY_FORMAT = '<I'

        self._buffer = buffer

        self.strings = []
        decoder = get_incremental_decoder('utf8')
        ip = offset
        while True:
            string_offset, = struct.unpack_from(OFFSET_ENTRY_FORMAT, buffer, ip)
            if string_offset == 0:
                break

            s, _ = decode_null_terminated(buffer,  # type: ignore
                                          decoder,
                                          offset=offset + string_offset)
            self.strings.append(s)

            ip += struct.calcsize(OFFSET_ENTRY_FORMAT)

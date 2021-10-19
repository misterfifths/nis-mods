import ctypes as C
from typing import Final

from astruct import typed_struct
from astruct.str_utils import (decode_null_terminated, encode_null_terminated,
                               get_incremental_decoder)
from astruct.type_hints import *

"""
NAME.DAT format:

Header: five 16-bit counts
Apparently there are 5 types of name. Each of these lengths is the number of
entries in the offset table that belongs to that type.
    type 0 = male names
    type 1 = female names
    other types unclear

Offset table: 16-bit offset per name
An offset from the beginning of the name table to the start of a string.
These are not in increasing address order, because they are grouped into the
5 types from the header.

Name table:
Back-to-back variable-length null-terminated shift-jis-encoded strings. For
some reason, each name seems to have twice as many bytes as actual ASCII
characters, padded with some number of ASCII spaces and 0x8140 (which is
shift-jis for U+3000 Ideographic Space).


The default NAME.DAT in the translation has this header:
    D000 CE00 CE00 CE00 6C00

    D000 = 208
    CE00 = 206
    CE00 = 206
    CE00 = 206
    6C00 = 108
    ----------
    total  934

That means the first 208 entries in the offset table belong to the first type
(male), then the next 206 are type 1 (female), and so on, for a total of 934
names. The whole offset table takes up 934 * 2 bytes, and the names themselves
begin at byte 10 (header) + 934 * 2 = 1,878.
"""


@typed_struct
class NameDatHeader(C.Structure):
    _pack_ = 1

    counts_by_type: CUInt16Array[5]

    @property
    def total_count(self) -> int:
        return sum(self.counts_by_type)


@typed_struct
class NameDatOffsetTableEntry(C.Structure):
    _pack_ = 1

    offset: CUInt16


class NameTable:
    STANDARD_FILENAME: Final = 'NAME.DAT'

    _header: NameDatHeader
    _offsets: CStructureArray[NameDatOffsetTableEntry]

    name_lists: list[list[str]]

    def __init__(self, buffer: WriteableBuffer, offset: int = 0) -> None:
        self._buffer = buffer
        self._header = NameDatHeader.from_buffer(buffer, offset)  # type: ignore

        offsets_tab_start = offset + C.sizeof(NameDatHeader)
        OffsetTableArrayClass = NameDatOffsetTableEntry * self._header.total_count
        self._offsets = OffsetTableArrayClass.from_buffer(buffer,  # type: ignore
                                                          offsets_tab_start)

        decoder = get_incremental_decoder('shift-jis')

        self.name_lists = []
        name_tab_start = offsets_tab_start + C.sizeof(OffsetTableArrayClass)

        start_idx = 0
        for type_count in self._header.counts_by_type:
            this_list: list[str] = []
            self.name_lists.append(this_list)
            for i in range(start_idx, start_idx + type_count):
                o = self._offsets[i]
                name, _ = decode_null_terminated(buffer,  # type: ignore
                                                 decoder,
                                                 offset=name_tab_start + o.offset)
                this_list.append(name)

            start_idx += type_count

    @classmethod
    def from_names(cls, name_lists: list[list[str]]) -> 'NameTable':
        if len(name_lists) != 5:
            raise ValueError('Argument must be a list of 5 lists')

        offset_tab = bytearray()
        name_tab = bytearray()

        cur_offset = 0
        for type_list in name_lists:
            for name in type_list:
                offset_obj = NameDatOffsetTableEntry(cur_offset)
                offset_tab.extend(bytes(offset_obj))  # type: ignore

                name_bytes = encode_null_terminated(name, 'shift-jis')
                name_tab.extend(name_bytes)

                cur_offset += len(name_bytes)

        buffer = bytearray(C.sizeof(NameDatHeader)) + offset_tab + name_tab
        header = NameDatHeader.from_buffer(buffer, 0)
        for i, type_list in enumerate(name_lists):
            header.counts_by_type[i] = len(type_list)

        return cls(buffer)

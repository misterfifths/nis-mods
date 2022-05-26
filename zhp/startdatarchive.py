import ctypes as C
import os
from dataclasses import dataclass
from typing import Final

from astruct import typed_struct
from astruct.ctypes_utils import get_bytes_for_field
from astruct.type_hints import *
from utils import ro_cached_property

from .items import ItemTable
from .skills import SkillTable
from .specials import SpecialSkillsTable


@typed_struct
class StartDatHeader(C.Structure):
    _pack_ = 1

    file_count: CUInt32


@typed_struct
class RawStartDatFileEntry(C.Structure):
    _pack_ = 1

    offset: CUInt32
    _raw_filename: CUInt8Array[27]
    _unk: CUInt8  # constant 0x7c?

    @property
    def filename(self) -> str:
        bs = get_bytes_for_field(self, '_raw_filename')
        bs_before_null = bs.split(b'\0', 1)[0]
        return bs_before_null.decode('shift-jis')

    # TODO? After decompression, the filenames are questionable. They wind up
    # with a ton of garbage after their nulls (repeated chunks of previous
    # filenames, mainly, like "whatever.dat\0at dat ..."). A few of them are
    # also not null-terminated, but we can't just use the NotNullTerminated()
    # annotation, because we need to stop at the first 0 byte or else we
    # sometimes get invalid shift-jis (hence the above filename property).
    # Is something subtly wrong with the LZS algorithm? I'd expect more obvious
    # errors elsewhere if so...


@dataclass(frozen=True)
class StartDatFileEntry:
    filename: str
    offset: int
    size: int


class StartDatArchive:
    STANDARD_FILENAME: Final = 'start.lzs'

    _buffer: WriteableBuffer
    _header: StartDatHeader

    _raw_files: CStructureArray[RawStartDatFileEntry]
    files: list[StartDatFileEntry]

    # Makes the assumption that the buffer is entirely the start.dat file;
    # the final file entry doesn't know where it ends, so we go to the end of
    # the buffer.
    def __init__(self, buffer: WriteableBuffer) -> None:
        self._buffer = buffer

        self._header = StartDatHeader.from_buffer(self._buffer)  # type: ignore[arg-type]

        file_entries_offset = C.sizeof(StartDatHeader)
        FileEntriesArrayClass = RawStartDatFileEntry * self._header.file_count
        self._raw_files = FileEntriesArrayClass.from_buffer(self._buffer,  # type: ignore
                                                            file_entries_offset)

        self._make_file_wrappers()

    def _make_file_wrappers(self) -> None:
        self.files = []

        # Entries only record the offset of their first byte, and not their
        # size. Assuming each file goes up to the start of the file after it,
        # or the end of the buffer for the final file.
        for i, raw_file in enumerate(self._raw_files):
            if i == len(self._raw_files) - 1:
                start_of_next_file = len(self._buffer)
            else:
                next_file = self._raw_files[i + 1]
                start_of_next_file = next_file.offset

            size = start_of_next_file - raw_file.offset
            self.files.append(StartDatFileEntry(raw_file.filename,
                                                raw_file.offset,
                                                size))

    def find_file(self, name: str) -> StartDatFileEntry:
        for file in self.files:
            if file.filename == name:
                return file

        raise KeyError(f'File {name!r} not found in archive')

    def extract_to_directory(self, dirname: str) -> None:
        for f in self.files:
            print(f'Extracting {f.filename} @ {f.offset:#x}: {f.size} bytes')
            with open(os.path.join(dirname, f.filename), 'wb') as o:
                o.write(self._buffer[f.offset:f.offset + f.size])

    @ro_cached_property
    def itemtab(self) -> ItemTable:
        file_entry = self.find_file(ItemTable.STANDARD_FILENAME)
        return ItemTable(self._buffer, file_entry.offset)

    @ro_cached_property
    def skilltab(self) -> SkillTable:
        file_entry = self.find_file(SkillTable.STANDARD_FILENAME)
        return SkillTable(self._buffer, file_entry.offset)

    @ro_cached_property
    def spectab(self) -> SpecialSkillsTable:
        file_entry = self.find_file(SpecialSkillsTable.STANDARD_FILENAME)
        return SpecialSkillsTable(self._buffer, file_entry.offset)

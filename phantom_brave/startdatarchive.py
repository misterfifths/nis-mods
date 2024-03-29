import ctypes as C
import os
from typing import Sequence, TypeVar

from astruct import typed_struct
from astruct.type_hints import *
from utils import CountedTable, ro_cached_property

from .classoritem import ClassOrItemTable
from .dungeoncategory import DungeonCategoryTable
from .fusioncompat import FusionCompatibilityTable
from .randomevent import RandomEventTable
from .skills import SkillTable
from .title import TitleTable

E = TypeVar('E', bound=AnyCType)


@typed_struct
class StartDatHeader(C.Structure):
    _pack_ = 1

    file_count: CUInt32  # TODO: this is probably 64 bits
    _zero: CUInt32Array[3]


@typed_struct
class RawStartDatFileEntry(C.Structure):
    _pack_ = 1

    raw_end_offset: CUInt32
    filename: CStr[28]


# TODO: combine this with RawStartDatFileEntry?
class StartDatFileEntry:
    filename: str
    offset: int
    size: int

    def __init__(self, raw_file: RawStartDatFileEntry, base_offset: int, file_offset: int) -> None:
        self.filename = raw_file.filename

        self.offset = file_offset
        self.size = base_offset + raw_file.raw_end_offset - file_offset


# This format is shared between Phantom Brave and La Pucelle. This base class
# isolates the game-independent parts.
class StartDatBase:
    _buffer: WriteableBuffer
    _base_offset: int
    _header: StartDatHeader
    _raw_files: C.Array[RawStartDatFileEntry]
    files: Sequence[StartDatFileEntry]

    def __init__(self, buffer: WriteableBuffer, offset: int = 0) -> None:
        self._buffer = buffer
        self._base_offset = offset

        self._header = StartDatHeader.from_buffer(self._buffer,  # type: ignore[arg-type]
                                                  self._base_offset)

        file_entries_offset = self._base_offset + C.sizeof(StartDatHeader)
        RawFileEntriesArray = RawStartDatFileEntry * self._header.file_count
        self._raw_files = RawFileEntriesArray.from_buffer(self._buffer,  # type: ignore[arg-type]
                                                          file_entries_offset)
        self._make_file_wrappers()

    def _make_file_wrappers(self) -> None:
        self.files = []

        # Entries only record the offset of their final byte, relative to the
        # beginning of the data. So the first file begins at the end of the
        # file listing:
        first_file_data_offset = (self._base_offset +
                                  C.sizeof(self._header) +
                                  C.sizeof(self._raw_files))
        offset = first_file_data_offset

        # Entries in the Phantom Brave start.dat are sorted by their end
        # offset. La Pucelle uses the exact same format but the entries aren't
        # sorted. For compatibility, we're just sorting unconditionally here.
        for raw_file in sorted(self._raw_files, key=lambda f: f.raw_end_offset):
            wrapper = StartDatFileEntry(raw_file, first_file_data_offset, offset)
            offset += wrapper.size

            self.files.append(wrapper)

    def find_file(self, name: str) -> StartDatFileEntry:
        for file in self.files:
            if file.filename == name:
                return file

        raise KeyError(f'File {name!r} not found in archive')

    def get_file_as_table(self, filename: str, element_cls: type[E]) -> CountedTable[E]:
        file_entry = self.find_file(filename)
        return CountedTable(element_cls, self._buffer, file_entry.offset)

    def extract_to_directory(self, dirname: str) -> None:
        for f in self.files:
            print(f'Extracting {f.filename} @ {f.offset:#x}: {f.size} bytes')
            with open(os.path.join(dirname, f.filename), 'wb') as o:
                o.write(self._buffer[f.offset:f.offset + f.size])


class StartDatArchive(StartDatBase):
    STANDARD_FILENAME = 'START.DAT'

    @ro_cached_property
    def skilltab(self) -> SkillTable:
        file_entry = self.find_file(SkillTable.STANDARD_FILENAME)
        return SkillTable(self._buffer, file_entry.offset)

    @ro_cached_property
    def cattab(self) -> DungeonCategoryTable:
        file_entry = self.find_file(DungeonCategoryTable.STANDARD_FILENAME)
        return DungeonCategoryTable(self._buffer, file_entry.offset)

    @ro_cached_property
    def classtab(self) -> ClassOrItemTable:
        file_entry = self.find_file(ClassOrItemTable.STANDARD_FILENAME)
        return ClassOrItemTable(self._buffer, file_entry.offset)

    @ro_cached_property
    def compattab(self) -> FusionCompatibilityTable:
        file_entry = self.find_file(FusionCompatibilityTable.STANDARD_FILENAME)
        return FusionCompatibilityTable(self._buffer, file_entry.offset)

    @ro_cached_property
    def titletab(self) -> TitleTable:
        file_entry = self.find_file(TitleTable.STANDARD_FILENAME)
        return TitleTable(self._buffer, file_entry.offset)

    @ro_cached_property
    def eventtab(self) -> RandomEventTable:
        file_entry = self.find_file(RandomEventTable.STANDARD_FILENAME)
        return RandomEventTable(self._buffer, file_entry.offset)

import ctypes as C
from typing import Annotated, ClassVar, Sequence, TypeVar
from astruct import typed_struct, CStrField, CField
from countedtable import CountedTable
from utils import AnyCType, WriteableBuffer, ro_cached_property
from skills import SkillTable
from dungeoncategory import DungeonCategoryTable
import os

E = TypeVar('E', bound=AnyCType)


@typed_struct
class StartDatHeader(C.Structure):
    _pack_: ClassVar[int] = 1

    file_count: Annotated[int, CField(C.c_uint32)]  # TODO: this is probably 64 bits
    _zero: Annotated[Sequence[int], CField(C.c_uint32 * 3)]


@typed_struct
class RawStartDatFileEntry(C.Structure):
    _pack_: ClassVar[int] = 1

    raw_end_offset: Annotated[int, CField(C.c_uint32)]
    filename: Annotated[str, CStrField(28)]


# TODO: combine this with RawStartDatFileEntry?
class StartDatFileEntry:
    filename: str
    offset: int
    size: int

    def __init__(self, raw_file: RawStartDatFileEntry, base_offset: int, file_offset: int) -> None:
        self.filename = raw_file.filename

        self.offset = file_offset
        self.size = base_offset + raw_file.raw_end_offset - file_offset


class StartDatArchive:
    STANDARD_FILENAME: ClassVar[str] = 'START.DAT'

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
        first_file_data_offset = self._base_offset + \
            C.sizeof(self._header) + \
            C.sizeof(self._raw_files)
        offset = first_file_data_offset
        for raw_file in self._raw_files:
            wrapper = StartDatFileEntry(raw_file, first_file_data_offset, offset)
            offset += wrapper.size

            self.files.append(wrapper)

    def find_file(self, name: str) -> StartDatFileEntry:
        for file in self.files:
            if file.filename == name:
                return file

        raise KeyError(f'File "{name}" not found in archive')

    def get_file_as_table(self, filename: str, element_cls: type[E]) -> CountedTable[E]:
        file_entry = self.find_file(filename)
        return CountedTable(element_cls, self._buffer, file_entry.offset)

    def extract_to_directory(self, dirname: str) -> None:
        for f in self.files:
            print(f'Extracting {f.filename} @ {f.offset:#x}: {f.size} bytes')
            with open(os.path.join(dirname, f.filename), 'wb') as o:
                o.write(self._buffer[f.offset:f.offset + f.size])

    @ro_cached_property
    def skilltab(self) -> SkillTable:
        file_entry = self.find_file(SkillTable.STANDARD_FILENAME)
        return SkillTable(self._buffer, file_entry.offset)

    @ro_cached_property
    def cattab(self) -> DungeonCategoryTable:
        file_entry = self.find_file(DungeonCategoryTable.STANDARD_FILENAME)
        return DungeonCategoryTable(self._buffer, file_entry.offset)

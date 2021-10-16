import ctypes as C
import os
from typing import Annotated, Final, TypeVar

from astruct import typed_struct
from astruct.type_hints import *
from utils import CountedTable, ro_cached_property

from .classes import ClassTable
from .items import ItemTable
from .skills import SkillTable
from .wish import WishTable

E = TypeVar('E', bound=AnyCType)


@typed_struct
class StartDatHeader(C.Structure):
    MAGIC: Final = 'DSARC FL'

    _pack_ = 1

    magic: Annotated[CStr[8], NotNullTerminated()]
    file_count: CUInt64

    def validate(self) -> None:
        if self.magic != self.MAGIC:
            raise ValueError(f'Invalid magic in START.DAT header: {self.magic}')


@typed_struct
class StartDatFileEntry(C.Structure):
    _pack_ = 1

    filename: CStr[40]
    size: CUInt32
    offset: CUInt32


class StartDatArchive:
    STANDARD_FILENAME: Final = 'START.KS4'

    _buffer: WriteableBuffer
    _header: StartDatHeader

    files: CStructureArray[StartDatFileEntry]

    def __init__(self, buffer: WriteableBuffer) -> None:
        self._buffer = buffer

        self._header = StartDatHeader.from_buffer(self._buffer)  # type: ignore[arg-type]
        self._header.validate()

        file_entries_offset = C.sizeof(StartDatHeader)
        FileEntriesArrayClass = StartDatFileEntry * self._header.file_count
        self.files = FileEntriesArrayClass.from_buffer(self._buffer,  # type: ignore
                                                       file_entries_offset)

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
    def wishtab(self) -> WishTable:
        file_entry = self.find_file(WishTable.STANDARD_FILENAME)
        return WishTable(self._buffer, file_entry.offset)

    @ro_cached_property
    def classtab(self) -> ClassTable:
        file_entry = self.find_file(ClassTable.STANDARD_FILENAME)
        return ClassTable(self._buffer, file_entry.offset)

    @ro_cached_property
    def itemtab(self) -> ItemTable:
        file_entry = self.find_file(ItemTable.STANDARD_FILENAME)
        return ItemTable(self._buffer, file_entry.offset)

    @ro_cached_property
    def skilltab(self) -> SkillTable:
        file_entry = self.find_file(SkillTable.STANDARD_FILENAME)
        return SkillTable(self._buffer, file_entry.offset)

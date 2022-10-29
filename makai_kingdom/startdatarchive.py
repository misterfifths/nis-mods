import ctypes as C
import os
from typing import Annotated, ByteString, TypeVar

from astruct import typed_struct
from astruct.type_hints import *
from utils import CountedTable, ro_cached_property

from .classes import ClassTable
from .items import ItemTable
from .names import NameTable
from .protection import ProtectionTable
from .skills import SkillTable
from .stringtable import StringTable
from .wish import WishTable

E = TypeVar('E', bound=AnyCType)


@typed_struct
class StartDatHeader(C.Structure):
    MAGIC = 'DSARC FL'

    _pack_ = 1

    magic: Annotated[CStr[8], NotNullTerminated()]
    file_count: CUInt64

    def validate(self) -> None:
        if self.magic != self.MAGIC:
            raise ValueError(f'Invalid magic in START.DAT header: {self.magic!r}')


@typed_struct
class StartDatFileEntry(C.Structure):
    _pack_ = 1

    filename: CStr[40]
    size: CUInt32
    offset: CUInt32


class StartDatArchive:
    STANDARD_FILENAME = 'START.KS4'

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

        raise KeyError(f'File {name!r} not found in archive')

    def get_file_as_table(self, filename: str, element_cls: type[E]) -> CountedTable[E]:
        file_entry = self.find_file(filename)
        return CountedTable(element_cls, self._buffer, file_entry.offset)

    def extract_to_directory(self, dirname: str) -> None:
        for f in self.files:
            print(f'Extracting {f.filename} @ {f.offset:#x}: {f.size} bytes')
            with open(os.path.join(dirname, f.filename), 'wb') as o:
                o.write(self._buffer[f.offset:f.offset + f.size])

    def archive_by_replacing_file(self,
                                  file_name: str,
                                  new_data: ByteString) -> 'StartDatArchive':
        """Create a new StartDatArchive by replacing the given file name with
        the given bytes. The new data does not need to have the same size as
        the old.
        """

        # TODO: share some code between this and the nearly identical method
        # on PSPFSArchive.

        file_to_replace = self.find_file(file_name)

        size_delta = len(new_data) - file_to_replace.size

        # Calculate the size of the new archive.
        # It's not safe to assume that the files are densely packed (i.e., we
        # can't just add up all the file sizes). Instead we have to find the
        # extent of the last file, after any offset shifting necessitated by
        # the replacement changing size.
        max_extent = 0
        for file in self.files:
            if file.filename == file_name:
                extent = file.offset + len(new_data)
            elif file.offset > file_to_replace.offset:
                extent = file.offset + size_delta + file.size
            else:
                extent = file.offset + file.size

            max_extent = max(max_extent, extent)

        res = bytearray(max_extent)

        new_header = StartDatHeader.from_buffer(res, 0)
        new_header.magic = StartDatHeader.MAGIC
        new_header.file_count = self._header.file_count
        new_header.validate()

        file_entries_offset = C.sizeof(StartDatHeader)
        FileEntriesArray = StartDatFileEntry * self._header.file_count
        new_files = FileEntriesArray.from_buffer(res, file_entries_offset)

        # build up the new list of file entries & contents
        for i in range(self._header.file_count):
            file = self.files[i]
            new_file: StartDatFileEntry = new_files[i]

            # copy over everything from the old entry
            new_file.filename = file.filename
            new_file.size = file.size
            new_file.offset = file.offset

            if file.filename == file_name:
                # update sizes if it's the file we're replacing
                new_file.size = len(new_data)

                # copy new data
                res[new_file.offset:new_file.offset + len(new_data)] = new_data
            else:
                if new_file.offset > file_to_replace.offset:
                    # shift the offset if it appears after the file we're
                    # replacing
                    new_file.offset += size_delta

                # copy old data
                old_data = self._buffer[file.offset:file.offset + file.size]
                res[new_file.offset:new_file.offset + file.size] = old_data

        return StartDatArchive(res)

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

    @ro_cached_property
    def nametab(self) -> NameTable:
        file_entry = self.find_file(NameTable.STANDARD_FILENAME)
        return NameTable(self._buffer, file_entry.offset)

    @ro_cached_property
    def prottab(self) -> ProtectionTable:
        file_entry = self.find_file(ProtectionTable.STANDARD_FILENAME)
        return ProtectionTable(self._buffer, file_entry.offset)

    @ro_cached_property
    def stringtab(self) -> StringTable:
        file_entry = self.find_file(StringTable.STANDARD_FILENAME)
        return StringTable(self._buffer, file_entry.offset)

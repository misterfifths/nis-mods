import ctypes as C
from contextlib import contextmanager
from pathlib import Path
from typing import Annotated, ByteString, Final, Iterator, Union

from astruct import typed_struct
from astruct.type_hints import *
from utils import private_mmap

from .startdatarchive import StartDatArchive
from .ykcmparchive import YKCMPArchive

# Despite having the same magic, this format is different than Phantom Brave's.
# See details here:
# https://gbatemp.net/threads/phantom-kingdom-portable-english-translation.365313/


@typed_struct
class PSPFSHeader(C.Structure):
    MAGIC: Final = 'PSPFS_V1'

    _pack_ = 1

    magic: Annotated[CStr[8], NotNullTerminated()]
    file_count: CUInt32
    _unk: CUInt32

    def validate(self) -> None:
        if self.magic != PSPFSHeader.MAGIC:
            raise ValueError(f'Invalid magic in PSPFS header: {self.magic!r}')


@typed_struct
class PSPFSFileEntry(C.Structure):
    _pack_ = 1

    filename: CStr[20]

    # This presumably has some meaning to the game, but is pretty useless for
    # us. Non-compressed files have a 0 here, and confusingly so do YKCMP-
    # compressed files like START.KS4 (their decompressed size is in the YKCMP
    # header).
    decompressed_size: CUInt32

    size: CUInt32
    offset: CUInt32


class PSPFSArchive:
    _buffer: WriteableBuffer
    _header: PSPFSHeader

    files: CStructureArray[PSPFSFileEntry]

    def __init__(self, buffer: WriteableBuffer) -> None:
        self._buffer = buffer

        self._header = PSPFSHeader.from_buffer(self._buffer)  # type: ignore[arg-type]
        self._header.validate()

        file_entries_offset = C.sizeof(PSPFSHeader)
        FileEntriesArrayClass = PSPFSFileEntry * self._header.file_count
        self.files = FileEntriesArrayClass.from_buffer(self._buffer,  # type: ignore
                                                       file_entries_offset)

    @classmethod
    @contextmanager
    def from_file(cls, path: Union[Path, str]) -> Iterator['PSPFSArchive']:
        with private_mmap(path) as mm:
            yield cls(mm)

    def find_file(self, name: str) -> PSPFSFileEntry:
        for file in self.files:
            if file.filename == name:
                return file

        raise KeyError(f'File {name!r} not found in archive')

    def get_start_dat(self) -> StartDatArchive:
        """Decompresses the START.KS4 file and returns the resulting
        StartDatArchive instance.

        Note that this is a copy of the decompressed data; changes to its bytes
        will not be automatically reflected in underlying buffer for the
        PSPFSArchive to which it belongs.
        """
        start_ks4 = self.find_file(StartDatArchive.STANDARD_FILENAME)
        start_arch = YKCMPArchive(self._buffer, start_ks4.offset)
        start_dat_buf = start_arch.decompress()
        return StartDatArchive(start_dat_buf)

    def archive_by_replacing_file(self,
                                  file_name: str,
                                  new_data: ByteString,
                                  decompressed_size: int = 0) -> 'PSPFSArchive':
        """Create a new PSPFSArchive by replacing the given file name with the
        given bytes. The new data does not need to have the same size as the
        old.

        You should probably leave decompresed_size as 0, even for YKMCP-
        compressed files.
        """

        # TODO: share some code between this and the nearly identical method
        # on StartDatArchive.

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

        new_header = PSPFSHeader.from_buffer(res, 0)
        new_header.magic = PSPFSHeader.MAGIC
        new_header.file_count = self._header.file_count
        new_header.validate()

        file_entries_offset = C.sizeof(PSPFSHeader)
        FileEntriesArray = PSPFSFileEntry * self._header.file_count
        new_files = FileEntriesArray.from_buffer(res, file_entries_offset)

        # build up the new list of file entries & contents
        for i in range(self._header.file_count):
            file = self.files[i]
            new_file = new_files[i]

            # copy over everything from the old entry
            new_file.filename = file.filename
            new_file.size = file.size
            new_file.decompressed_size = file.decompressed_size
            new_file.offset = file.offset

            if file.filename == file_name:
                # update sizes if it's the file we're replacing
                new_file.size = len(new_data)
                new_file.decompressed_size = decompressed_size

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

        return PSPFSArchive(res)

import ctypes as C
from typing import Annotated, Final

from astruct import typed_struct
from astruct.type_hints import *

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
            raise ValueError(f'Invalid magic in PSPFS header: "{self.magic}"')


@typed_struct
class PSPFSFileEntry(C.Structure):
    _pack_ = 1

    filename: CStr[20]
    decompressed_size: CUInt32  # for non-compressed files, this equals size
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

    def find_file(self, name: str) -> PSPFSFileEntry:
        for file in self.files:
            if file.filename == name:
                return file

        raise KeyError(f'File "{name}" not found in archive')

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

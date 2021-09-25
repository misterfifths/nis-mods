from typing import Annotated, Final
import ctypes as C
from astruct import typed_struct
from astruct.type_hints import *
from startdatarchive import StartDatArchive
from utils import ro_cached_property

# TODO: enable switching between these
PSP_FILENAME_LEN = 20
PC_SWITCH_FILENAME_LEN = 40

# Thanks to xdanieldzd's Scarlet project for helping me work out details on the
# PSPFS container format. See in particular:
# https://github.com/xdanieldzd/Scarlet/blob/master/Scarlet.IO.ContainerFormats/PSPFSv1.cs


@typed_struct
class PSPFSHeader(C.Structure):
    MAGIC: Final = 'PSPFS_V1'

    _pack_ = 1

    magic: Annotated[CStr[8], NotNullTerminated()]
    file_count: CUInt64

    def validate(self) -> None:
        if self.magic != self.MAGIC:
            raise ValueError(f'Invalid magic in PSPFS header: "{self._header.magic}"')


@typed_struct
class PSPFSFileEntry(C.Structure):
    _pack_ = 1

    filename: CStr[PC_SWITCH_FILENAME_LEN]
    _unk: CUInt8Array[4]  # TODO: confirm this is there on PSP
    size: CUInt32
    offset: CUInt32


class PSPFSArchive:
    _buffer: WriteableBuffer
    _header: PSPFSHeader
    files: C.Array[PSPFSFileEntry]  # TODO: Type as a Sequence?

    def __init__(self, buffer: WriteableBuffer) -> None:
        self._buffer = buffer

        self._header = PSPFSHeader.from_buffer(self._buffer)  # type: ignore[arg-type]
        self._header.validate()

        file_entries_offset = C.sizeof(PSPFSHeader)
        FileEntriesArray = PSPFSFileEntry * self._header.file_count
        self.files = FileEntriesArray.from_buffer(self._buffer,  # type: ignore[arg-type]
                                                  file_entries_offset)

    def find_file(self, name: str) -> PSPFSFileEntry:
        for file in self.files:
            if file.filename == name:
                return file

        raise KeyError(f'File "{name}" not found in archive')

    @ro_cached_property
    def start_dat(self) -> StartDatArchive:
        file_entry = self.find_file(StartDatArchive.STANDARD_FILENAME)
        return StartDatArchive(self._buffer, file_entry.offset)

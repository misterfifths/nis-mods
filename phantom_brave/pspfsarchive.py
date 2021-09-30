from typing import Annotated, Final, Protocol, Union
import ctypes as C
from astruct import typed_struct
from astruct.type_hints import *
from utils import ro_cached_property
from .startdatarchive import StartDatArchive


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


class PSPFSFileEntry(Protocol):
    filename: str
    size: int
    offset: int


@typed_struct
class _PSPFSFileEntry_PCAndSwitch(C.Structure):
    _pack_ = 1
    filename: CStr[40]
    _unk: CUInt8Array[4]
    size: CUInt32
    offset: CUInt32


@typed_struct
class _PSPFSFileEntry_PSP(C.Structure):
    _pack_ = 1
    filename: CStr[24]
    # It may be that the unknown 4-byte field on PC/Switch is also present here
    # and just always zero.
    size: CUInt32
    offset: CUInt32


class PSPFSArchive:
    _buffer: WriteableBuffer
    _header: PSPFSHeader

    files: CArray[PSPFSFileEntry, Union[_PSPFSFileEntry_PCAndSwitch, _PSPFSFileEntry_PSP]]

    def __init__(self, buffer: WriteableBuffer, is_pc_or_switch: bool = True) -> None:
        self._buffer = buffer

        self._header = PSPFSHeader.from_buffer(self._buffer)  # type: ignore[arg-type]
        self._header.validate()

        file_entries_offset = C.sizeof(PSPFSHeader)

        FileEntryClass: type[PSPFSFileEntry]
        if is_pc_or_switch:
            FileEntryClass = _PSPFSFileEntry_PCAndSwitch
        else:
            FileEntryClass = _PSPFSFileEntry_PSP

        FileEntriesArrayClass = FileEntryClass * self._header.file_count
        self.files = FileEntriesArrayClass.from_buffer(self._buffer,  # type: ignore
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

import ctypes as C
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Annotated, Final, Iterator, Union

from astruct import typed_struct
from astruct.type_hints import *
from utils import private_mmap

from .lzsarchive import LZSArchive
from .startdatarchive import StartDatArchive

# Thanks yet again to xdanieldzd's Scarlet project for serving as a reference
# to this format. See in particular
# https://github.com/xdanieldzd/Scarlet/blob/master/Scarlet.IO.ContainerFormats/NISPACK.cs


@typed_struct
class NISPACKHeader(C.Structure):
    MAGIC: Final = 'NISPACK\0'

    _pack_ = 1

    magic: Annotated[CStr[8], NotNullTerminated()]
    big_endian_flag: CUInt32
    file_count: CUInt32

    def validate(self) -> None:
        if self.magic != self.MAGIC:
            raise ValueError(f'Invalid magic in NISPACK header: {self.magic!r}')

        if self.big_endian_flag != 0:
            raise ValueError('Only little-endian NISPACK files are supported')


@typed_struct
class NISPACKFileEntry(C.Structure):
    _pack_ = 1

    filename: CStr[32]
    offset: CUInt32
    size: CUInt32
    _unk: CUInt32


class NISPACKArchive:
    _buffer: WriteableBuffer
    _header: NISPACKHeader

    files: CStructureArray[NISPACKFileEntry]

    def __init__(self, buffer: WriteableBuffer) -> None:
        self._buffer = buffer

        self._header = NISPACKHeader.from_buffer(self._buffer)  # type: ignore[arg-type]
        self._header.validate()

        file_entries_offset = C.sizeof(NISPACKHeader)
        FileEntriesArrayClass = NISPACKFileEntry * self._header.file_count
        self.files = FileEntriesArrayClass.from_buffer(self._buffer,  # type: ignore
                                                       file_entries_offset)

    @classmethod
    @contextmanager
    def from_file(cls, path: Union[Path, str]) -> Iterator['NISPACKArchive']:
        with private_mmap(path) as mm:
            yield cls(mm)

    def find_file(self, name: str) -> NISPACKFileEntry:
        for file in self.files:
            if file.filename == name:
                return file

        raise KeyError(f'File {name!r} not found in archive')

    def extract_to_directory(self, dirname: str) -> None:
        for f in self.files:
            print(f'Extracting {f.filename} @ {f.offset:#x}: {f.size} bytes')
            with open(os.path.join(dirname, f.filename), 'wb') as o:
                o.write(self._buffer[f.offset:f.offset + f.size])

    def get_start_dat(self) -> StartDatArchive:
        """Decompresses the start.lzs file and returns the resulting
        StartDatArchive instance.

        Note that this is a copy of the decompressed data; changes to its bytes
        will not be automatically reflected in underlying buffer for the
        NISPACKArchive to which it belongs.
        """
        start_lzs = self.find_file(StartDatArchive.STANDARD_FILENAME)
        start_arch = LZSArchive(self._buffer, start_lzs.offset)
        start_dat_buf = start_arch.decompress()
        return StartDatArchive(start_dat_buf)

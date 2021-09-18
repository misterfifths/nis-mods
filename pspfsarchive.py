import ctypes as C
from typing import Annotated, ClassVar, Optional
from astruct import PackedAStruct, CField, CStrField
from utils import WriteableBuffer


# TODO: enable switching between these
PSP_FILENAME_LEN = 24
PC_SWITCH_FILENAME_LEN = 44

# Thanks to xdanieldzd's Scarlet project for helping me work out details on the
# PSPFS container format. See in particular:
# https://github.com/xdanieldzd/Scarlet/blob/master/Scarlet.IO.ContainerFormats/PSPFSv1.cs


class PSPFSHeader(PackedAStruct):
    MAGIC: ClassVar[str] = 'PSPFS_V1'

    magic: Annotated[str, CStrField(8, null_terminated=False)]
    file_count: Annotated[int, CField(C.c_uint64)]

    def validate(self) -> None:
        if self.magic != self.MAGIC:
            raise ValueError(f'Invalid magic in PSPFS header: "{self._header.magic}"')


class PSPFSFileEntry(PackedAStruct):
    filename: Annotated[str, CStrField(PC_SWITCH_FILENAME_LEN)]
    size: Annotated[int, CField(C.c_uint32)]
    offset: Annotated[int, CField(C.c_uint32)]


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

    def find_file(self, name: str) -> Optional[PSPFSFileEntry]:
        for file in self.files:
            if file.filename == name:
                return file

        return None
import ctypes as C
import os
import struct
from contextlib import contextmanager
from pathlib import Path
from typing import Annotated, Final, Iterable, Iterator, Optional, Union

import zstandard as zstd

from astruct import typed_struct
from astruct.str_utils import decode_null_terminated, get_incremental_decoder
from astruct.type_hints import *
from utils import CountedTable, private_mmap, ro_cached_property

from .startdatarchive import StartDatArchive

"""
There are quite a few variations on VFS3 files. The Prinny Presents re-release
of La Pucelle seems to use one very close to the Switch release of Ni No Kuni
2, with some simplifications (no zstd dictionaries). Huge debt to masagrator
for figuring out the details (link below).

zstd compressed data is stored in the .vfs file with its frame header and
each block header stripped. The framing must reconstituted from a list of
the size of each block, which are stored out-of-band (called here "chunk
sizes").

References:
https://github.com/masagrator/NXGameScripts/blob/main/Ni%20No%20Kuni%202/VFS_Unpacker.py
https://zenhax.com/viewtopic.php?t=15413
http://aluigi.altervista.org/bms/killer7_vfs.bms
"""


@typed_struct
class VFSHeader(C.Structure):
    MAGIC: Final = 'VFS3'

    _pack_ = 1

    magic: Annotated[CStr[4], NotNullTerminated()]
    version: CUInt32

    def validate(self) -> None:
        if self.magic != self.MAGIC:
            raise ValueError(f'Invalid magic in VFS header: {self.magic!r}')


@typed_struct
class VFSFolderEntry(C.Structure):
    _pack_ = 1

    crc: CUInt32
    folder_id: CInt32
    parent_folder_id: CInt32
    first_subfolder_id: CInt32
    subfolder_count: CUInt32
    _unk: CUInt32
    file_count: CUInt32

    def path(self, folders: Iterable['VFSFolderEntry'], names: 'VFSNameTable') -> str:
        if self.parent_folder_id == -1:
            # A root folder. The name is the empty string in our example.
            return names.name_for_folder(self.folder_id)

        parent = None
        for folder in folders:
            if folder.folder_id == self.parent_folder_id:
                parent = folder
                break

        if parent is None:
            raise ValueError(f'Folder {self.folder_id:#x} has an unknown parent folder id '
                             f'{self.prev_id:#x}')

        res = parent.path(folders, names)
        if len(res) > 0:
            res += '/'  # don't add the slash if the root dir name was empty
        res += names.name_for_folder(self.folder_id)
        return res


@typed_struct
class VFSFileEntry(C.Structure):
    _pack_ = 1

    # This is an address relative to the end of the subheader, not from the
    # start of the file. See VFSArchive below for details.
    data_offset: CUInt64

    compressed_size: CUInt64
    decompressed_size: CUInt64
    crc: CUInt32
    file_id: CInt32
    parent_folder_id: CInt32

    # Values for this field in La Pucelle are 0, 3, b, 1b.
    # The Killer 7 BMS file says it's compressed if bit 1 is set. If bit 0
    # is also set, it's zstd; otherwise it's zlib.
    # Not clear on what bits 3 and 4 mean.
    flags: CUInt16

    # -1 means no dictionary. Everything in La Pucelle is -1
    decompression_dict_id: CInt16

    @property
    def is_compressed(self) -> bool:
        return self.flags & 2 == 2

    @property
    def is_zstd_compressed(self) -> bool:
        return self.is_compressed and self.flags & 1 == 1

    @property
    def is_zlib_compressed(self) -> bool:
        return self.is_compressed and not self.is_zstd_compressed


@typed_struct
class VFSSubheader(C.Structure):
    _pack_ = 1

    chunk_data_offset: CUInt64
    decompression_dict_offset: CUInt64
    name_data_offset: CUInt64


class VFSNameTable:
    file_names: list[str]
    folder_names: list[str]

    def __init__(self, buffer: WriteableBuffer, offset: int = 0) -> None:
        self.file_names = []
        self.folder_names = []

        decoder = get_incremental_decoder('utf_16_le')

        # A 32-bit LE count, followed by that many back-to-back null-terminated
        # UTF-16 LE file names.
        file_count, = struct.unpack_from('<I', buffer, offset)
        offset += struct.calcsize('I')
        for _ in range(file_count):
            s, offset = decode_null_terminated(buffer,  # type: ignore
                                               decoder,
                                               offset=offset)
            self.file_names.append(s)

        # And then the same for folder names.
        folder_count, = struct.unpack_from('<I', buffer, offset)
        offset += struct.calcsize('I')
        for _ in range(folder_count):
            s, offset = decode_null_terminated(buffer,  # type: ignore
                                               decoder,
                                               offset=offset)
            self.folder_names.append(s)

    def name_for_folder(self, folder_id: int) -> str:
        return self.folder_names[folder_id]

    def name_for_file(self, file_id: int) -> str:
        return self.file_names[file_id]


class VFSChunkSizesTable:
    chunk_sizes: list[list[int]]

    def __init__(self, buffer: WriteableBuffer, offset: int = 0) -> None:
        self.chunk_sizes = []

        # 32-bit LE size for the whole table (excluding these bytes themselves)
        byte_len, = struct.unpack_from('<I', buffer, offset)

        offset += struct.calcsize('I')
        end = offset + byte_len

        while offset < end:
            # Each set of chunk sizes is prefixed with another 32-bit LE int,
            # the length in bytes of the sizes for this file. It can be zero.
            chunk_info_byte_len, = struct.unpack_from('<I', buffer, offset)
            offset += struct.calcsize('I')

            if offset + chunk_info_byte_len > end:
                raise ValueError(f'Chunk info at {offset:#x}-{offset + chunk_info_byte_len:#x} '
                                 f'extends past the end of the chunk table @ {end:#x}')

            # The actual chunk sizes are just back-to-back LE int32s.
            chunk_bytes = buffer[offset:offset + chunk_info_byte_len]
            sizes = list(i for i, in struct.iter_unpack('<i', chunk_bytes))
            self.chunk_sizes.append(sizes)

            offset += chunk_info_byte_len

    def chunk_sizes_for_file(self, file_id: int) -> list[int]:
        # File IDs are not sequential in La Pucelle's VFS file, but there are
        # chunk size lists for every integer between 0 and the maximum ID
        # (empty for unused file IDs). So we can just look it up like this:
        return self.chunk_sizes[file_id]


def zstd_frame_header(decompressed_size: Optional[int] = None) -> bytes:
    MAGIC = 0xFD2FB528

    # This format is documented here:
    # https://github.com/facebook/zstd/blob/dev/doc/zstd_compression_format.md#frame_header_descriptor

    if decompressed_size is not None:
        # We're just hard-coding a 32-bit content size.
        if decompressed_size < 0 or decompressed_size > 0xffffffff:
            raise ValueError('Decompressed_size must be a positive integer that fits in 32 bits')

    fcs_field_size_flag = 2  # 32-bit content size field follows the descriptor
    if decompressed_size is None:
        fcs_field_size_flag = 0

    single_segment_flag = 0
    content_checksum_flag = 0
    dict_id_size_flag = 0

    descriptor_byte = (fcs_field_size_flag << 6 |
                       single_segment_flag << 5 |
                       content_checksum_flag << 2 |
                       dict_id_size_flag)

    window_descriptor = 0x88  # 128mb (not magic; anything large enough is ok)

    if decompressed_size is None:
        return struct.pack('<IBB', MAGIC, descriptor_byte, window_descriptor)

    return struct.pack('<IBBI', MAGIC, descriptor_byte, window_descriptor, decompressed_size)


def zstd_block_header(size: int, is_compressed: bool = True, is_last_block: bool = False) -> bytes:
    # This format is documented here:
    # https://github.com/facebook/zstd/blob/dev/doc/zstd_compression_format.md#blocks

    if size < 0 or size > 0x3fffff:
        raise ValueError('Block size must be a positive integer that fits in 21 bits')

    # I don't think VFS supports RLE blocks; treating all compressed blocks as
    # zstd (type 2).
    block_type = 2 if is_compressed else 0

    packed = (size << 3 |
              block_type << 1 |
              int(is_last_block))

    return packed.to_bytes(length=3, byteorder='little')


def reassemble_zstd_file(decompressed_size: int,
                         compressed_data: bytes,
                         chunk_sizes: list[int]) -> bytearray:
    res = bytearray(zstd_frame_header(decompressed_size))

    expected_total_chunk_len = 0
    chunk_offset = 0
    for i, raw_chunk_len in enumerate(chunk_sizes):
        # If the chunk length is negative, the chunk is not compressed
        is_compressed = raw_chunk_len >= 0

        chunk_len = abs(raw_chunk_len)
        expected_total_chunk_len += chunk_len

        is_last_block = i == len(chunk_sizes) - 1

        block_header = zstd_block_header(chunk_len,
                                         is_compressed=is_compressed,
                                         is_last_block=is_last_block)
        res.extend(block_header)
        res.extend(compressed_data[chunk_offset:chunk_offset + chunk_len])
        chunk_offset += chunk_len

    if expected_total_chunk_len != len(compressed_data):
        raise ValueError(f'Compressed data size {len(compressed_data)} does not match the total '
                         f'size of the chunks ({expected_total_chunk_len})')

    return res


class VFSArchive:
    _buffer: WriteableBuffer
    _header: VFSHeader
    _folders: CountedTable[VFSFolderEntry]
    _files: CountedTable[VFSFileEntry]
    _subhead: VFSSubheader
    _nametab: VFSNameTable
    _chunktab: VFSChunkSizesTable
    _chunk_offset_origin: int

    _files_by_path: dict[str, VFSFileEntry]

    def __init__(self, buffer: WriteableBuffer) -> None:
        self._buffer = buffer

        # We start with a simple header.
        self._header = VFSHeader.from_buffer(buffer)  # type: ignore
        self._header.validate()

        # Then a table of folder entries, prefixed with a 32-bit count
        # (conveniently a common structure for us; we can reuse CountedTable)
        self._folders = CountedTable(VFSFolderEntry,
                                     buffer,
                                     offset=C.sizeof(VFSHeader),
                                     double_counted=False)

        file_count_from_foldertab = sum(f.file_count for f in self._folders)

        # Then a table of file entries, again prefixed with a count
        filetab_offset = (C.sizeof(VFSHeader) +
                          C.sizeof(C.c_uint32) +
                          len(self._folders) * C.sizeof(VFSFolderEntry))

        self._files = CountedTable(VFSFileEntry,
                                   buffer,
                                   offset=filetab_offset,
                                   double_counted=False)

        if len(self._files) != file_count_from_foldertab:
            raise ValueError(f'Folder structures say there should be {file_count_from_foldertab} '
                             f'files, but found {len(self._files)}')

        # Then there's the subheader, a sort of table of contents of the
        # remainder of the file.
        subhead_offset = (filetab_offset +
                          C.sizeof(C.c_uint32) +
                          len(self._files) * C.sizeof(VFSFileEntry))

        self._subhead = VFSSubheader.from_buffer(buffer,  # type: ignore
                                                 subhead_offset)

        # File data offsets are relative to the nearest multiple of 16 bytes
        # after the end of the subheader.
        subhead_end = subhead_offset + C.sizeof(VFSSubheader)
        self._chunk_offset_origin = subhead_end
        if subhead_end % 16 != 0:
            self._chunk_offset_origin = subhead_end + (16 - (subhead_end % 16))

        # Assemble the table of file and folder names from the offset in the
        # subheader.
        self._nametab = VFSNameTable(buffer, offset=self._subhead.name_data_offset)

        # There should be exactly enough names for the files and folders.
        if len(self._files) != len(self._nametab.file_names):
            raise ValueError(f'Found {len(self._nametab.file_names)} file names for '
                             f'{len(self._files)} files')

        if len(self._folders) != len(self._nametab.folder_names):
            raise ValueError(f'Found {len(self._nametab.folder_names)} folder names for '
                             f'{len(self._folders)} folders')

        # And finally the table of chunk sizes for each file, which also has
        # its offset in the subheader.
        self._chunktab = VFSChunkSizesTable(buffer, offset=self._subhead.chunk_data_offset)

        # There should be enough entries in the chunk table for every file id
        max_file_id = max(f.file_id for f in self._files)
        if len(self._chunktab.chunk_sizes) <= max_file_id:
            raise ValueError(f'The maximum file id is {max_file_id}, but there are only '
                             f'{len(self._chunktab.chunk_sizes)} entries in the chunk size table')

        # We do not support decompression dictionaries, the other notable field
        # in the subheader. They're unused in La Pucelle's VFS, and the sanity
        # check function below will notice if a file purports to use them.

        self._file_sanity_checks()
        self._build_path_lookup()

    def _file_sanity_checks(self) -> None:
        for f in self._files:
            # zlib compression is not supported
            if f.is_zlib_compressed:
                raise ValueError(f'File {self._nametab.name_for_file(f.file_id)!r} (id '
                                 f'{f.file_id:#x}) has unsupported compression flag {f.flags:#x}')

            if f.is_compressed:
                # Compressed files should have chunks, and the total size of
                # those chunks should equal the file's compressed_size.
                chunk_sizes = self._chunktab.chunk_sizes_for_file(f.file_id)
                if len(chunk_sizes) == 0:
                    raise ValueError(f'File {self._nametab.name_for_file(f.file_id)!r} (id '
                                     f'{f.file_id:#x}) is compressed but has no chunks')

                compressed_size_from_chunks = sum(abs(s) for s in chunk_sizes)
                if compressed_size_from_chunks != f.compressed_size:
                    raise ValueError(f'File {self._nametab.name_for_file(f.file_id)!r} (id '
                                     f'{f.file_id:#x}) should have {f.compressed_size} bytes of '
                                     f'compressed data, but its chunks are '
                                     f'{compressed_size_from_chunks} bytes')
            else:
                # Uncompressed files should have no chunks, and should have
                # the same compressed and decompressed size.
                if f.decompressed_size != f.compressed_size:
                    raise ValueError(f'File {self._nametab.name_for_file(f.file_id)!r} (id '
                                     f'{f.file_id:#x}) is uncompressed but has a decompressed '
                                     f'size {f.decompressed_size} != compressed size '
                                     f'{f.compressed_size}')

                chunk_sizes = self._chunktab.chunk_sizes_for_file(f.file_id)
                if len(chunk_sizes) != 0:
                    raise ValueError(f'File {self._nametab.name_for_file(f.file_id)!r} (id '
                                     f'{f.file_id:#x}) is uncompressed but has {len(chunk_sizes)} '
                                     'chunks')

            # Decompression dictionaries are not supported
            if f.decompression_dict_id != -1:
                raise ValueError(f'File {self._nametab.name_for_file(f.file_id)!r} (id '
                                 f'{f.file_id:#x}) has unsupported compression dict id '
                                 f'{f.decompression_dict_id:#x}')

    def _folder_for_id(self, folder_id: int) -> VFSFolderEntry:
        for folder in self._folders:
            if folder.folder_id == folder_id:
                return folder

        raise ValueError(f'Unknown folder id {folder_id:#x}')

    def _path_for_file(self, file: VFSFileEntry) -> str:
        name = self._nametab.name_for_file(file.file_id)
        folder = self._folder_for_id(file.parent_folder_id)
        return folder.path(self._folders, self._nametab) + '/' + name

    def _build_path_lookup(self) -> None:
        self._files_by_path = {}
        for f in self._files:
            self._files_by_path[self._path_for_file(f)] = f

    def find_file(self, path: str) -> VFSFileEntry:
        entry = self._files_by_path.get(path)
        if entry is None:
            raise KeyError(f'No known file with path {path!r}')

        return entry

    @classmethod
    @contextmanager
    def from_file(cls, path: Union[Path, str]) -> Iterator['VFSArchive']:
        with private_mmap(path) as mm:
            yield cls(mm)

    def dump_files(self) -> None:
        for f in self._files:
            name = self._nametab.name_for_file(f.file_id)
            folder = self._folder_for_id(f.parent_folder_id)
            path = folder.path(self._folders, self._nametab) + '/' + name

            print(f'{f.file_id:04x} {path}: {f.decompressed_size} bytes')

    def _raw_bytes_for_file(self, file: VFSFileEntry) -> bytes:
        return self._buffer[self._chunk_offset_origin + file.data_offset:
                            self._chunk_offset_origin + file.data_offset + file.compressed_size]

    def bytes_for_file(self, file: VFSFileEntry) -> bytes:
        raw_bytes = self._raw_bytes_for_file(file)
        if not file.is_zstd_compressed:
            return raw_bytes

        chunk_sizes = self._chunktab.chunk_sizes_for_file(file.file_id)
        zst_bytes = reassemble_zstd_file(file.decompressed_size, raw_bytes, chunk_sizes)

        return zstd.decompress(zst_bytes, max_output_size=file.decompressed_size)

    def bytes_for_path(self, path: str) -> bytes:
        return self.bytes_for_file(self.find_file(path))

    def extract_to_directory(self, dirname: str) -> None:
        for f in self._files:
            path = os.path.join(dirname, self._path_for_file(f))
            print(f'Extracting {path}: {f.decompressed_size} bytes')

            dest_dir = os.path.dirname(path)
            os.makedirs(dest_dir, exist_ok=True)
            with open(path, 'wb') as o:
                o.write(self.bytes_for_file(f))

    @ro_cached_property
    def start_dat(self) -> StartDatArchive:
        start_dat_bytes = bytearray(self.bytes_for_path(StartDatArchive.STANDARD_PATH))
        return StartDatArchive(start_dat_bytes)

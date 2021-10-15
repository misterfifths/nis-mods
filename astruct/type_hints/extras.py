import ctypes as C
from typing import TYPE_CHECKING, Sequence, Union

from .ctypes_aliases import AnyCType

if TYPE_CHECKING:
    import mmap

"""
TODO: Better WriteableBuffer type? Feels like a MutableSequence[int] should be
fine, but there's some weirdness between the types struct.unpack_from and
ctypes.Structure.from_buffer want.
"""

# Intended to represent any type that can be passed to a ctypes from_buffer
# method, but there are some issues in the stubs that make that hard.
WriteableBuffer = Union[bytearray, memoryview, 'mmap.mmap']

# A single element of the _fields_ attribute of a ctypes.Structure or Union.
CStructureField = Union[tuple[str, type[AnyCType]], tuple[str, type[AnyCType], int]]

# The entire _fields_ attribute of a ctypes.Structure or Union.
CStructureFields = Sequence[CStructureField]

CStructureOrUnion = Union[C.Structure, C.Union]

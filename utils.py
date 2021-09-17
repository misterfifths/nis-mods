from typing import Union
from mmap import mmap
import ctypes as C

"""
TODO:
- Better WriteableBuffer type? Feels like a MutableSequence[int] should be
fine, but there's some weirdness between the types struct.unpack_from and
ctypes.Structure.from_buffer want.
"""


WriteableBuffer = Union[bytearray, memoryview, mmap]
AnyCType = Union[C._SimpleCData, C.Array, C.Structure, C.Union]

from typing import Any, Union
from mmap import mmap
import ctypes as C

# ctypes._SimpleCData is private, but we have no other good way to reference
# all the C types from that module.
# pyright: reportPrivateUsage=none

"""
TODO:
- Better WriteableBuffer type? Feels like a MutableSequence[int] should be
fine, but there's some weirdness between the types struct.unpack_from and
ctypes.Structure.from_buffer want.
"""


WriteableBuffer = Union[bytearray, memoryview, mmap]

# _SimpleCData isn't actually subscriptable like this; the typing stubs just
# invented that functionality. Quoting it like this prevents the error we get
# if we try to actually subscript it.
AnyCType = Union['C._SimpleCData[Any]', C.Array[Any], C.Structure, C.Union]

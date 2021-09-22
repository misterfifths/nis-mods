from typing import Union
import mmap

"""
TODO: Better WriteableBuffer type? Feels like a MutableSequence[int] should be
fine, but there's some weirdness between the types struct.unpack_from and
ctypes.Structure.from_buffer want.
"""

# Intended to represent any type that can be passed to a ctypes from_buffer
# method, but there are some issues in the stubs that make that hard.
WriteableBuffer = Union[bytearray, memoryview, mmap.mmap]

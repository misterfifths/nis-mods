from typing import Sequence, TypeVar, Iterator, Union, overload
import ctypes as C
import struct
from astruct import PackedAStruct
from mmap import mmap

"""
TODO?
- A MutableSequence implementation for CountedTable.
- The E TypeVar is too narrow. It would be fine for the elements of a counted
table to be simple ctypes like c_uint16, but the common base type (_CData) is
not easily accessible.
- Avoid the struct.unpack_from call, maybe? A header struct that we subclass?
Probably not worth it.
- I'm pretty sure CountedTable.__contains__ doesn't really work, because ctypes
Structures don't handle equality in a normal way. Probably not a big deal.
- Better WriteableBuffer type? Feels like a MutableSequence[int] should be
fine, but there's some weirdness between the types struct.unpack_from and
ctypes.Structure.from_buffer want.
- Is it a problem that CountedTable itself is not a Structure? The current
approach prevents us from embedding it in other Structures, or in an array.
"""

E = TypeVar('E', bound=C.Structure)
WriteableBuffer = Union[bytearray, memoryview, mmap]


def structFactory(element_cls: type[E], length: int) -> type[C.Structure]:
    """Creates and returns a ctypes.Structure subclass representing a
    length-prefixed table of length instances of element_cls.
    """
    class RawCountedTable(PackedAStruct):
        capacity: C.c_uint32
        entry_count: C.c_uint32
        entries: element_cls * length  # type: ignore[valid-type]
        # mypy doesn't seem to grok that a C.Structure subclass multiplied by
        # an int results in a type. Can't say that I blame it.

    return RawCountedTable


class CountedTable(Sequence[E]):
    """A length-prefixed sequence of instances of a particular C structure.

    This class is a sequence, and is thus iterable and indexable.
    """
    _raw: C.Structure

    def __init__(self, element_cls: type[E], buffer: WriteableBuffer, offset: int = 0) -> None:
        """Create a CountedTable instance consisting of elements of type
        element_cls starting at the given offset in buffer.

        element_cls must be a ctypes.Structure subclass, and the buffer must be
        writeable (e.g. a bytearray, mmap, or memoryview).
        """
        # TODO: unclear on the difference between these values. I assume one is
        # capacity and the other is the actual length, but in every example I
        # have, they're equal.
        capacity, entry_count = struct.unpack_from('II', buffer, offset)
        if capacity != entry_count:
            raise ValueError(f'Capacity ({capacity}) is not equal to entry count ({entry_count})!')

        struct_cls = structFactory(element_cls, entry_count)

        # The stub for Structure.from_buffer disagrees slightly with our
        # WriteableBuffer. We'll just ignore type errors.
        self._raw = struct_cls.from_buffer(buffer, offset)  # type: ignore[arg-type]

    def __iter__(self) -> Iterator[E]:
        return iter(self._raw.entries)

    def __len__(self) -> int:
        return len(self._raw.entries)

    def __contains__(self, x: object) -> bool:
        return x in self._raw.entries

    @overload
    def __getitem__(self, idx: int) -> E: ...

    @overload
    def __getitem__(self, idx: slice) -> list[E]: ...

    def __getitem__(self, idx: Union[slice, int]) -> Union[list[E], E]:
        return self._raw.entries.__getitem__(idx)

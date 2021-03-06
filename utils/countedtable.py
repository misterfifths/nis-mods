import ctypes as C
from typing import Iterator, Protocol, Sequence, TypeVar, Union, overload

from astruct import typed_struct
from astruct.type_hints import *

"""
TODO?
- A MutableSequence implementation for CountedTable.
- Is it a problem that CountedTable itself is not a Structure? The current
approach prevents us from embedding it in other Structures, or in an array.
"""

E = TypeVar('E', bound=AnyCType)


class CountedTableHeader(Protocol):
    entry_count: int


@typed_struct
class _DoubleCountedTableHeader(C.Structure):
    _pack_ = 1

    # TODO: unclear on the difference between these values. I assume one is
    # capacity and the other is the actual length, but in every example I
    # have, they're equal.
    capacity: CUInt32
    entry_count: CUInt32

    def validate(self) -> None:
        if self.capacity != self.entry_count:
            raise ValueError(f'Capacity ({self.capacity}) is not equal to entry count'
                             f' ({self.entry_count})!')


@typed_struct
class _SingleCountedTableHeader(C.Structure):
    _pack_ = 1

    entry_count: CUInt32

    def validate(self) -> None:
        pass


class CountedTable(Sequence[E]):
    """A length-prefixed sequence of instances of a particular C structure.

    This class is a sequence, and is thus iterable and indexable.
    """
    _header: CountedTableHeader
    _entries: C.Array[E]

    def __init__(self,
                 element_cls: type[E],
                 buffer: WriteableBuffer,
                 offset: int = 0,
                 double_counted: bool = True) -> None:
        """Create a CountedTable instance consisting of elements of type
        element_cls starting at the given offset in buffer.

        element_cls must be a ctypes type (e.g. a Structure subclass), and the
        buffer must be writeable (e.g. a bytearray, mmap, or memoryview).

        If the table has a header with a capacity and count, double_counted
        should be True. If it only has a single count in the header, pass
        False for that parameter.
        """
        HeaderClass = _DoubleCountedTableHeader if double_counted else _SingleCountedTableHeader
        self._header = HeaderClass.from_buffer(buffer, offset)  # type: ignore[arg-type]
        self._header.validate()

        EntriesArray: type[C.Array[E]]
        EntriesArray = element_cls * self._header.entry_count  # type: ignore[operator, assignment]
        entries_offset = offset + C.sizeof(HeaderClass)
        self._entries = EntriesArray.from_buffer(buffer,  # type: ignore[arg-type]
                                                 entries_offset)

    def __iter__(self) -> Iterator[E]:
        return iter(self._entries)

    def __len__(self) -> int:
        return len(self._entries)

    def __contains__(self, x: object) -> bool:
        # Despite what the stubs say, ctypes.Arrays do support this method. It
        # just doesn't do what you might expect. It works fine for arrays of
        # simple ctypes, but for arrays of Structures, which have a weird/
        # nonexistant notion of equality, it pretty much always returns False.
        # TODO: improve on that somehow?
        return x in self._entries  # type: ignore[operator]

    @overload
    def __getitem__(self, idx: int) -> E:
        ...

    @overload
    def __getitem__(self, idx: slice) -> Sequence[E]:
        ...

    def __getitem__(self, idx: Union[slice, int]) -> Union[Sequence[E], E]:  # type: ignore
        return self._entries.__getitem__(idx)

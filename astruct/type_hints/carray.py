# pyright: reportUnusedClass=none

from typing import ClassVar, Iterable, Iterator, Protocol, TypeVar, overload
from abc import abstractmethod
from .ctypes_aliases import AnyCType

_T = TypeVar('_T')
_CT = TypeVar('_CT', bound=AnyCType)


# Ideally this would start with Sequence and add things from there, but after
# Collection, for some reason the sequence hierarchy classes cease being
# Protocols. And also some of them (Sized) come with a metaclass.
class CArray(Iterable[_T], Protocol[_T, _CT]):
    """A protocol representing the behavior of ctypes.Array.

    A ctypes.Array is tricky because it relates two types: the underlying
    ctype representing the raw data, and the outward-facing Python type for it.
    Sometimes, as in the case of Structure and Union subclasses, these types
    are the same. But for the basic types, they always differ (e.g. an array of
    c_uint8s is actually experienced as a field of ints).

    So, CArray is generic on two types: first the Python type, then the ctype.
    The underlying ctype is accessible via the _type_ class variable.

    The interface is effectively a fixed-length array whose elements can be
    changed. Some methods are missing, including index.

    This type can be used on typed_structs by annotating a class attribute
    like so:
        grades: Annotated[CArray[int, c_uint8], Length(20)]

    The Length metadata is mandatory in this use case. For all simple ctypes,
    there are shorter aliases in the type_hints module. This is equivalent to
    the above, for instance:
        grades: CUInt8Array[20]

    The long-hand form is still useful for arrays of custom Structure or Union
    subclasses.
    """
    _type_: ClassVar[type[_CT]]

    @overload
    @abstractmethod
    def __getitem__(self, i: int) -> _T: ...

    @overload
    @abstractmethod
    def __getitem__(self, s: slice) -> list[_T]: ...

    @overload
    @abstractmethod
    def __setitem__(self, i: int, o: _T) -> None: ...

    @overload
    @abstractmethod
    # Setting slices is allowed, but throws if the length doesn't match.
    def __setitem__(self, s: slice, o: Iterable[_T]) -> None: ...

    @abstractmethod
    def __len__(self) -> int: ...

    @abstractmethod
    def __contains__(self, x: object) -> bool: ...

    @abstractmethod
    def __iter__(self) -> Iterator[_T]: ...

    @abstractmethod
    def __reversed__(self) -> Iterator[_T]: ...

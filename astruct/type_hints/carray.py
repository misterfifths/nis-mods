# pyright: reportUnusedClass=none

import ctypes as C
from abc import abstractmethod
from typing import ClassVar, Iterable, Iterator, Protocol, TypeVar, overload

from .ctypes_aliases import AnyCType

_T = TypeVar('_T')
_CT = TypeVar('_CT', bound=AnyCType)
_CS = TypeVar('_CS', bound=C.Structure)
_CU = TypeVar('_CU', bound=C.Union)


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

    For arrays of Structures or Unions, you can use the CStructureArray and
    CUnionArray types as shorthand; they only take one type argument.
    """
    # Re: the below ignore - there is ongoing discussion on whether this should
    # be valid. See https://github.com/python/mypy/issues/5144.
    _type_: ClassVar[type[_CT]]  # type: ignore

    @overload
    @abstractmethod
    def __getitem__(self, i: int) -> _T:
        ...

    @overload
    @abstractmethod
    def __getitem__(self, s: slice) -> list[_T]:
        ...

    @overload
    @abstractmethod
    def __setitem__(self, i: int, o: _T) -> None:
        ...

    @overload
    @abstractmethod
    # Setting slices is allowed, but throws if the length doesn't match.
    def __setitem__(self, s: slice, o: Iterable[_T]) -> None:
        ...

    @abstractmethod
    def __len__(self) -> int:
        ...

    @abstractmethod
    def __contains__(self, x: object) -> bool:
        ...

    @abstractmethod
    def __iter__(self) -> Iterator[_T]:
        ...

    @abstractmethod
    def __reversed__(self) -> Iterator[_T]:
        ...


class CStructureArray(CArray[_CS, _CS], Protocol[_CS]):
    """CStructureArray and CUnionArray are protocols representing a
    ctypes.Array of ctypes.Structures or Unions.

    The types are shorthand for a CArray where the ctype of the underlying data
    and the exposed Python type are one and the same, which is the case for
    Structure and Union subclasses. If MyStruct is a Structure, these two
    types are exactly equivalent:
        CArray[MyStruct, MyStruct]
        CStructureArray[MyStruct]

    CStructureArray and CUnionArray can be used as type hints on attributes in
    typed_struct classes, just like CArray.
    """
    pass


class CUnionArray(CArray[_CU, _CU], Protocol[_CU]):
    pass


CUnionArray.__doc__ = CStructureArray.__doc__

# pyright: reportUnusedClass=none

from typing import Any, Iterable, Iterator, Protocol, TypeVar, overload
from typing import _GenericAlias  # type: ignore
from abc import abstractmethod
from .ctypes_aliases import IntCType, FloatCType

_T = TypeVar('_T')
_IntCT_co = TypeVar('_IntCT_co', bound=IntCType, covariant=True)
_FloatCT_co = TypeVar('_FloatCT_co', bound=FloatCType, covariant=True)


# Ideally this would start with Sequence and add things from there, but after
# Collection, for some reason the sequence hierarchy classes cease being
# Protocols. And also some of them (Sized) come with a metaclass.
class CArray(Iterable[_T], Protocol[_T]):
    """A protocol representing the behavior of ctypes.Array.

    Effectively a fixed-length array whose elements can be changed. Some
    methods are missing, including index.
    """
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


class _CIntArray(CArray[int], Protocol[_IntCT_co]):
    def __class_getitem__(cls, params: Any) -> _GenericAlias:  # type: ignore
        # Not much use in typechecking; these are our internal classes
        return _GenericAlias(cls, params)  # type: ignore


class _CFloatArray(CArray[float], Protocol[_FloatCT_co]):
    def __class_getitem__(cls, params: Any) -> _GenericAlias:  # type: ignore
        return _GenericAlias(cls, params)  # type: ignore

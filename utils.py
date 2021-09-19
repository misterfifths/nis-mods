from abc import abstractmethod
from typing import Any, Callable, ClassVar, Generic, Optional, Sequence, TypeVar, Union
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


T = TypeVar('T')
RT = TypeVar('RT')


class ro_cached_property(Generic[T, RT]):
    """A decorator for a read-only, deletable cached property.

    Like cached_property but read-only and clearable.
    Like stacked @property and @cached but lighter weight and clearable.

    The decorated instance method is run only if its value is not cached. An
    existing cached value may be cleared by deleting the property, thus
    allowing the getter method to run again.

    Values are cached as attributes on the enclosing class, so this decorator
    can only be used on classes that allow the addition of abritrary
    attributes.
    """
    CACHE_ATTR_PREFIX: ClassVar[str] = "__cached_"

    func: Callable[[T], RT]
    attr_name: Optional[str]

    def __init__(self, func: Callable[[T], RT]) -> None:
        self.func = func
        self.attr_name = None
        self.__doc__ = func.__doc__

    def __set_name__(self, owner: Any, name: str) -> None:
        if self.attr_name is None:
            self.attr_name = name
        elif name != self.attr_name:
            raise TypeError("Cannot assign the same ro_cached_property to two different names "
                            f"({self.attr_name!r} and {name!r}).")

    def __get__(self, instance: T, owner: Any = None) -> RT:
        if self.attr_name is None:
            raise TypeError("Cannot use ro_cached_property instance without calling __set_name__ "
                            "on it.")

        cache_attr_name = self.CACHE_ATTR_PREFIX + self.attr_name
        try:
            return getattr(instance, cache_attr_name)
        except AttributeError:
            val = self.func(instance)
            setattr(instance, cache_attr_name, val)
            return val

    def __delete__(self, instance: T) -> None:
        if self.attr_name is None:
            raise TypeError("Cannot use ro_cached_property instance without calling __set_name__ "
                            "on it.")

        cache_attr_name = self.CACHE_ATTR_PREFIX + self.attr_name
        try:
            delattr(instance, cache_attr_name)
        except AttributeError:
            pass


class FixedLengthMutableSequence(Sequence[T]):
    """A Sequence whose items can be set but whose length cannot be changed."""
    @abstractmethod
    def __setitem__(self, i: int, o: T) -> None: ...

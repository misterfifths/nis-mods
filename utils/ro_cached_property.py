from typing import Any, Callable, Generic, Optional, TypeVar

_T = TypeVar('_T')
_RT = TypeVar('_RT')

"""
TODO: not strictly sure why this was necessary. Stacked @property and @cache
seemed to be hanging on to their values for too long. I got errors trying to
close an mmap if there were ctypes.Structure into it via that approach. This
seems to fix those and is simple enough, but still.
"""


class ro_cached_property(Generic[_T, _RT]):
    """A decorator for a read-only, deletable cached property.

    Like cached_property but read-only and clearable.
    Like stacked @property and @cache but lighter weight and clearable.

    The decorated instance method is run only if its value is not cached. An
    existing cached value may be cleared by deleting the property, thus
    allowing the getter method to run again.

    Values are cached as attributes on the enclosing class, so this decorator
    can only be used on classes that allow the addition of abritrary
    attributes.
    """
    CACHE_ATTR_PREFIX = "__cached_"

    func: Callable[[_T], _RT]
    attr_name: Optional[str]

    def __init__(self, func: Callable[[_T], _RT]) -> None:
        self.func = func  # type: ignore[assignment]  # mypy bug #708
        self.attr_name = None
        self.__doc__ = func.__doc__

    def __set_name__(self, owner: Any, name: str) -> None:
        if self.attr_name is None:
            self.attr_name = name
        elif name != self.attr_name:
            raise TypeError("Cannot assign the same ro_cached_property to two different names "
                            f"({self.attr_name!r} and {name!r}).")

    def __get__(self, instance: _T, owner: Any = None) -> _RT:
        if self.attr_name is None:
            raise TypeError("Cannot use ro_cached_property instance without calling __set_name__ "
                            "on it.")

        cache_attr_name = self.CACHE_ATTR_PREFIX + self.attr_name
        try:
            return getattr(instance, cache_attr_name)
        except AttributeError:
            val = self.func(instance)  # type: ignore[call-arg]  # mypy #708
            setattr(instance, cache_attr_name, val)
            return val

    def __delete__(self, instance: _T) -> None:
        if self.attr_name is None:
            raise TypeError("Cannot use ro_cached_property instance without calling __set_name__ "
                            "on it.")

        cache_attr_name = self.CACHE_ATTR_PREFIX + self.attr_name
        try:
            delattr(instance, cache_attr_name)
        except AttributeError:
            pass

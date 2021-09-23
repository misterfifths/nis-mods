from typing import Annotated, Any, Optional, TypeVar
import typing

_T = TypeVar('_T')


def hint_is_specialized(hint: Any, target: Any) -> bool:
    """Checks if a type hint is a specialized version of target.

    E.g., hint_is_specialized(ClassVar[int], ClassVar) is True.

    isinstance will invoke type-checking, which this methods sidesteps.
    Behavior is undefined for simple type hints that don't take a type
    argument, like Any or a bare type.
    """
    return typing.get_origin(hint) is target


def first_annotated_md_of_type(note: Any, md_cls: type[_T]) -> Optional[_T]:
    """If note is an Annotated type hint, returns the first piece of metadata
    belonging to it that is an instance of md_cls.

    If note is not an Annotated instance, or if it has no such metadata,
    returns None.
    """
    if not hint_is_specialized(note, Annotated):  # type: ignore[arg-type]
        return None

    # The first arg is the underlying type; skip it
    metadata = typing.get_args(note)[1:]
    for md in metadata:
        if isinstance(md, md_cls):
            return md

    return None

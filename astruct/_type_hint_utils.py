from typing import Annotated, Any, Optional, TypeVar
import typing

_T = TypeVar('_T')


def hint_is(note: Any, note_cls: type) -> bool:
    """Checks if a type hint is an instance of note_cls. Subclasses are not
    considered.

    isinstance will invoke type-checking, but this method answers the question
    of if, e.g., an Any type hint is literally the typing.Any class.
    """
    # Not sure if this is the best way to sidestep type checking, but it works
    # for now.
    return typing.get_origin(note) is note_cls


def first_annotated_md_of_type(note: Any, md_cls: type[_T]) -> Optional[_T]:
    """If note is an Annotated type annotation, returns the first piece of
    metadata belonging to it that is an instance of md_cls.

    If note is not an Annotated instance, or if it has no such metadata,
    returns None.
    """
    if not hint_is(note, Annotated):  # type: ignore[arg-type]
        return None

    # The first arg is the underlying type; skip it
    metadata = typing.get_args(note)[1:]
    for md in metadata:
        if isinstance(md, md_cls):
            return md

    return None

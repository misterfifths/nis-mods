from typing import Annotated, Any, Optional
import typing
from dataclasses import dataclass
from ._type_hint_utils import hint_is_specialized, first_annotated_md_of_type
from .type_hints.metadata import Length
from .type_hints.carray import CArray
from .type_hints.ctypes_aliases import AnyCType, is_ctype_subclass


@dataclass
class CArrayAttr:
    """Represents the configuration of a CArray attribute on a typed_struct."""
    length: int
    ctype: type[AnyCType]

    @classmethod
    def _from_type_hint(cls,
                        attr_name: str,
                        hint: Any,
                        unannotated_hint: Any) -> Optional['CArrayAttr']:
        """Construct an instance from the given type hint if possible.

        Retrieves relevant metadata (e.g. Length) from the hint if it is
        Annotated.

        Raises a TypeError in a variety of misconfiguration scenarios. If the
        hint is not somehow related to CArray (either an Annotated or one of
        the helpers), returns None.
        """
        if unannotated_hint is CArray:
            # This is either a bare CArray with no length or an Annotated
            # version of the same. Either way it's wrong.
            raise TypeError('CArray type hints must use Annotated with the Length metadata')

        origin: Optional[Any] = typing.get_origin(unannotated_hint)
        if origin is None:
            return None

        if hint_is_specialized(hint, Annotated) and origin is CArray:
            return cls._from_annotated(hint, unannotated_hint)

        if origin is CArray:
            # This must be an un-Annotated CArray
            raise TypeError('CArray type hints must use Annotated with the Length metadata')

        return None

    @classmethod
    def _from_annotated(cls, hint: Any, unannotated_hint: Any) -> 'CArrayAttr':
        type_args = typing.get_args(unannotated_hint)
        if len(type_args) != 2:
            raise TypeError('CArray requires two type arguments')

        ctype = type_args[1]
        if not is_ctype_subclass(ctype):
            raise TypeError('The second type argument to CArray must be a ctype')

        if length_md := first_annotated_md_of_type(hint, Length):
            return cls(length_md.length, ctype)

        raise TypeError('Annotated CArrays must have the Length metadata applied')

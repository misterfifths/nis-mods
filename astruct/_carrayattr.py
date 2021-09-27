from typing import Annotated, Any, Optional
import typing
from dataclasses import dataclass
from ._type_hint_utils import hint_is_specialized, first_annotated_md_of_type, issubclass_static
from .type_hints.metadata import Length
from .type_hints.carray import CArray, CStructureArray
from .type_hints.ctypes_aliases import AnyCType, is_ctype_subclass


@dataclass
class CArrayAttr:
    """Represents the configuration of a CArray attribute on a typed_struct."""
    length: int
    ctype: type[AnyCType]

    @classmethod
    def from_type_hint(cls,
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
        if typing.get_origin(unannotated_hint) is None:
            # The actual type is unspecialized. If it's a CArray subclass,
            # this means we either have a bare CArray hint with no length, or
            # an Annotated version of the same, both of which are errors.
            if issubclass_static(unannotated_hint, CArray):
                raise TypeError('CArray type hints must use Annotated with the Length metadata')

        origin: Optional[Any] = typing.get_origin(unannotated_hint)
        if origin is None:
            return None

        origin_is_carray = issubclass_static(origin, CArray)

        if hint_is_specialized(hint, Annotated) and origin_is_carray:
            return cls._from_annotated(hint, unannotated_hint)

        if origin_is_carray:
            # This must be an un-Annotated CArray
            raise TypeError('CArray type hints must use Annotated with the Length metadata')

        return None

    @classmethod
    def _get_ctype_from_hint(cls, unannotated_hint: Any) -> Optional[type[AnyCType]]:
        is_structure_array = hint_is_specialized(unannotated_hint, CStructureArray)

        type_args = typing.get_args(unannotated_hint)

        ctype = None
        if is_structure_array and len(type_args) == 1:
            ctype = type_args[0]
        elif not is_structure_array and len(type_args) == 2:
            ctype = type_args[1]

        if ctype is not None and is_ctype_subclass(ctype):
            return ctype

        return None

    @classmethod
    def _from_annotated(cls, hint: Any, unannotated_hint: Any) -> 'CArrayAttr':
        # hint is known to be an Annotated[CArray, ...] (or subclass)
        # TODO: assuming it's either CArray or CStructureArray, and hardcoding
        # the type parameters for each. Do that more generically?
        is_structure_array = hint_is_specialized(unannotated_hint, CStructureArray)

        ctype = cls._get_ctype_from_hint(unannotated_hint)
        if ctype is None:
            if is_structure_array:
                raise TypeError('CStructureArray and CUnionArray require a single ctype type '
                                'parameter')
            else:
                raise TypeError('CArray requires two type parameters, the second of which must '
                                'be a ctype')

        if length_md := first_annotated_md_of_type(hint, Length):
            return cls(length_md.length, ctype)

        raise TypeError('Annotated CArrays must have the Length metadata applied')

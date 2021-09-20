from typing import Annotated, Any, Optional
import typing
from dataclasses import dataclass
from ._type_hint_utils import hint_is, first_annotated_md_of_type
from .type_hints.metadata import Length
from .type_hints.carray import CArray, _CIntArray, _CFloatArray
from .type_hints.ctypes_aliases import AnyCType, is_ctype_subclass

# pyright: reportPrivateUsage=none


@dataclass
class CArrayAttr:
    """Represents the configuration of a CArray attribute on a typed_struct."""
    length: int
    ctype: type[AnyCType]

    @classmethod
    def _is_array_hint(cls, hint: Any, unannotated_hint: Any) -> bool:
        origin: Optional[type] = typing.get_origin(unannotated_hint)

        if origin is None:
            return False

        # Probably an annotated CArray (e.g. Annotated[CArray[MyStruct], ...])
        if origin is CArray:
            return True

        # Our helper aliases, like CUInt8Array, will have CArray in the mro of
        # their origin
        if CArray in origin.mro():
            return True

        return False

    @classmethod
    def from_type_hint(cls, hint: Any, unannotated_hint: Any) -> Optional['CArrayAttr']:
        """Construct an instance from the given type hint if possible.

        Retrieves relevant metadata (e.g. Length) from the hint if it is
        Annotated.

        Raises a TypeError in a variety of misconfiguration scenarios. If the
        hint is not somehow related to CArray (either an Annotated or one of
        the helpers), returns None.
        """
        if not cls._is_array_hint(hint, unannotated_hint):
            return None

        if hint_is(hint, Annotated):  # type: ignore
            return cls._from_annotated(hint, unannotated_hint)

        return cls._from_helper_type(hint, unannotated_hint)

    @classmethod
    def _from_annotated(cls, hint: Any, unannotated_hint: Any) -> 'CArrayAttr':
        type_args = typing.get_args(unannotated_hint)
        if len(type_args) != 1:
            raise TypeError('CArray requires exactly one type argument')

        ctype = type_args[0]
        if not is_ctype_subclass(ctype):
            raise TypeError('The type argument to CArray must be a ctype')

        if length_md := first_annotated_md_of_type(hint, Length):
            return cls(length_md.length, ctype)

        raise TypeError('Annotated CArrays must have the Length metadata applied')

    @classmethod
    def _from_helper_type(cls, hint: Any, unannotated_hint: Any) -> 'CArrayAttr':
        type_args = typing.get_args(unannotated_hint)
        if len(type_args) != 1:
            raise TypeError('C array type hints require a single length argument')

        length = type_args[0]
        if not isinstance(length, int):
            raise TypeError('The length for C array type hints must be an int')

        # The ctype is part of the verbatim base type of the hint's origin
        origin = typing.get_origin(unannotated_hint)
        orig_bases: tuple[Any] = origin.__orig_bases__  # type: ignore

        ctype: Optional[type[AnyCType]] = None
        for orig_base in orig_bases:
            if ctype := cls._get_ctype_from_array_base(orig_base):
                break

        if ctype is None:
            # should never happen
            raise RuntimeError('Could not find the ctype from C array helper hint '
                               f'{unannotated_hint}')

        return cls(length, ctype)

    @classmethod
    def _get_ctype_from_array_base(cls, base: Any) -> Optional[type[AnyCType]]:
        ARRAY_HELPER_BASES: set[type] = {_CIntArray, _CFloatArray}

        origin = typing.get_origin(base)
        if origin not in ARRAY_HELPER_BASES:
            return None

        # not doing any sanity checking here; these are our internal types
        return typing.get_args(base)[0]

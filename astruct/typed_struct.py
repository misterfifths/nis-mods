# pyright: reportPrivateUsage=none

import ctypes as C
import typing
from typing import Any, ClassVar, Generic, TypeVar

from ._carrayattr import CArrayAttr
from ._cfieldattr import CFieldAttr
from ._cstrattr import CStrAttr
from ._type_hint_utils import hint_is_specialized
from .type_hints.extras import CStructureField, CStructureOrUnion

_CSU = TypeVar('_CSU', bound=CStructureOrUnion)


class _TypedStructBuilder(Generic[_CSU]):
    ATTR_NAME_BLACKLIST = {'_anonymous_', '_pack_'}

    target_cls: type[_CSU]
    hints: dict[str, Any]
    unannotated_hints: dict[str, Any]

    fields: list[CStructureField]

    def __init__(self, target_cls: type[_CSU]) -> None:
        self.target_cls = target_cls
        self.hints = typing.get_type_hints(target_cls, include_extras=True)
        self.unannotated_hints = typing.get_type_hints(target_cls, include_extras=False)

    def wrap(self) -> type[_CSU]:
        self.fields = []

        if hasattr(self.target_cls, '_fields_'):
            raise TypeError('typed_struct should not be used with classes that already have a '
                            '_fields_ attribute')

        for attr_name, hint in self.hints.items():
            if attr_name in self.ATTR_NAME_BLACKLIST:
                continue

            if hint_is_specialized(hint, ClassVar):  # type: ignore[arg-type]
                continue

            if hasattr(self.target_cls, attr_name) and attr_name.upper() != attr_name:
                # This attr was actually given a value in the class definition.
                # If it doesn't look like a constant, throw to be safe.
                raise ValueError(f'typed_struct applied to a class with an attr {attr_name} with '
                                 'a value. Name it in all caps if it is a constant, or annotate '
                                 'it with ClassVar if it is a class-level variable.')

            unannotated_hint = self.unannotated_hints[attr_name]

            if cfldattr := CFieldAttr.from_type_hint(attr_name, hint, unannotated_hint):
                self._apply_cfield(attr_name, cfldattr)
            elif cstrattr := CStrAttr.from_type_hint(attr_name, hint, unannotated_hint):
                self._apply_cstr_field(attr_name, cstrattr)
            elif carrayattr := CArrayAttr.from_type_hint(attr_name, hint, unannotated_hint):
                self._apply_array_field(attr_name, carrayattr)

        self.target_cls._fields_ = self.fields[:]  # type: ignore[attr-defined]
        return self.target_cls

    def _apply_cfield(self, name: str, cfldattr: CFieldAttr) -> None:
        cfld = cfldattr.cfield
        if cfld.bitwidth is not None:
            self.fields.append((name, cfld.ctype, cfld.bitwidth))
        else:
            self.fields.append((name, cfld.ctype))

    def _apply_array_field(self, name: str, carrayattr: CArrayAttr) -> None:
        array_type = carrayattr.ctype * carrayattr.length
        self.fields.append((name, array_type))

    def _apply_cstr_field(self, name: str, cstrattr: CStrAttr) -> None:
        # The field is given a prefixed name:
        self.fields.append((cstrattr.raw_field_name, cstrattr.array_ctype))

        # And the actual attr is set to cstrattr, which is a descriptor:
        setattr(self.target_cls, name, cstrattr)


def typed_struct(cls: type[_CSU]) -> type[_CSU]:
    """A decorator to allow declaring ctypes.Structure subclasses with type
    annotations instead of _fields_.

    To use, decorate a Structure subclass with your fields as class-level
    attributes, using CField annotations or CStr. Omit the _fields_ attribute
    entirely; typed_struct will generate it for you.

    An example:

    @typed_struct
    class Player(Structure):
        level: Annotated[int, CField(c_uint16)]
        hp: Annotated[int, CField(c_uint16)]
        skill_aptitudes: Annotated[Sequence[int], CField(c_uint8 * 8)]
        name: CStr[16]
    """
    if not issubclass(cls, (C.Structure, C.Union)):
        raise TypeError('@typed_struct can only be applied to subclasses of ctypes.Structure or '
                        'ctypes.Union')

    return _TypedStructBuilder(cls).wrap()  # type: ignore  # TODO: wtf mypy?

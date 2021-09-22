from typing import ClassVar, Final, Generic, Any, TypeVar
import typing
from ._type_hint_utils import hint_is
from .type_hints.extras import CStructureOrUnion, CStructureField
from ._cstrattr import CStrAttr
from ._carrayattr import CArrayAttr
from ._cfieldattr import CFieldAttr



_CSU = TypeVar('_CSU', bound=CStructureOrUnion)


class _TypedStructBuilder(Generic[_CSU]):
    CSTR_RAW_BYTES_PREFIX: Final = '_raw_'
    ATTR_NAME_BLACKLIST: Final = {'_anonymous_', '_pack_'}

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

            if hint_is(hint, ClassVar):  # type: ignore[arg-type]
                continue

            if hint_is(hint, Final):
                continue

            unannotated_hint = self.unannotated_hints[attr_name]

            if cfldattr := CFieldAttr.from_hint(hint, unannotated_hint):
                self._apply_cfield(attr_name, cfldattr)
            elif cstrattr := CStrAttr.from_type_hint(hint, unannotated_hint):
                self._apply_cstr_field(attr_name, cstrattr)
            elif carrayattr := CArrayAttr.from_type_hint(hint, unannotated_hint):
                self._apply_array_field(attr_name, carrayattr)

        self.target_cls._fields_ = self.fields[:]
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
        field_name = self.CSTR_RAW_BYTES_PREFIX + name
        self.fields.append((field_name, cstrattr.ctype * cstrattr.max_length))

        self._add_string_prop(name, field_name, cstrattr)

    def _add_string_prop(self, prop_name: str, field_name: str, cstr: CStrAttr) -> None:
        """Adds a property to transparently read and write a ctypes.c_char
        array as a str.

        Arguments:
        name: The name of the property. The underlying ctypes array is assumed
            to be a prefixed version of this string.
        cstr: The CStrAttr instance defining the behavior of the string.
        """
        def getter(self: Any) -> str:
            return cstr.bytes_to_str(getattr(self, field_name))

        def setter(self: Any, value: str) -> None:
            setattr(self, field_name, cstr.str_to_bytes(value))

        # TODO: just give CStrAttr __get__ and __set__?

        setattr(self.target_cls, prop_name, property(getter, setter))


def typed_struct(cls: type[_CSU]) -> type[_CSU]:
    """A decorator to allow declaring ctypes.Structure subclasses with type
    annotations instead of _fields_.

    To use, decorate a Structure subclass with your fields as class-level
    attributes, annotated with either CField or CStrField. Omit the _fields_
    attribute entirely; typed_struct will generate it for you.

    The decorator also adds transparent string properties for fixed-length
    c_char arrays via the CStrField metadata.

    An example:

    @typed_struct
    class Player(Structure):
        level: Annotated[int, CField(c_uint16)]
        hp: Annotated[int, CField(c_uint16)]
        skill_aptitudes: Annotated[Sequence[int], CField(c_uint8 * 8)]
        name: Annotated[str, CStrField(16)]
    """
    return _TypedStructBuilder(cls).wrap()

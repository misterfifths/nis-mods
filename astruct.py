from typing import Annotated, ClassVar, Generic, Optional, Any, Sequence, TypeVar, Union
import typing
import ctypes as C
from dataclasses import dataclass
from utils import AnyCType

"""
TODO:
- less verbose annotations!
"""

CStructureField = Union[tuple[str, type[AnyCType]], tuple[str, type[AnyCType], int]]
CStructOrUnion = Union[C.Structure, C.Union]

T = TypeVar('T')
CSU = TypeVar('CSU', bound=CStructOrUnion)


@dataclass(frozen=True)
class CField:
    """Annotation metadata for a field of an AStruct class.

    Use by annotating a class attribute in an AStruct like this:
        level: Annotated[int, CField(c_uint32)]

    Attributes:
    ctype: The underlying ctypes data type for the field. Must be one of the
        simple types in the ctypes module, a Structure, Union, Array, or
        subclass thereof.
    bitwidth: For integral ctypes, the width of the field in bits. See details
        in the documentation for the third element of the _fields_ tuples of a
        ctypes.Structure.

    For an array of c_chars that represent a fixed-length string, consider
    using CStrField, which handles the conversion between bytes and str.
    """
    ctype: type[AnyCType]
    bitwidth: Optional[int] = None


@dataclass(frozen=True)
class CStrField:
    """Annotation metadata for a C-string member of an AStruct class.

    Use by annotating a class attribute in an AStruct like this:
        name: Annotated[str, CStrField(32, encoding='utf-8')]

    The resulting property will transparently convert between bytes and str
    using the given encoding and optionally enforcing null-termination.
    Attempts to set the property to a string that is too long will result in an
    IndexError.

    Attributes:
    max_length: The total number of bytes in the string, including the null
        byte if null_terminated is True.
    encoding: The encoding of the string. Defaults: 'shift-jis'.
    errors: What to do if an error is encountered in en/decoding the string.
        One of the constants from bytes.decode. Default: 'strict'.
    null_terminated: True if the string is terminated with a null byte. A zero
        byte will be appended to the string when it is stored in memory, and
        everything after the first zero will be ignored when converting to a
        string. Default: True.
    """
    max_length: int
    encoding: str = 'shift-jis'
    errors: str = 'strict'
    null_terminated: bool = True

    def bytes_to_str(self, bs: bytes) -> str:
        """Convert the given bytes to a string, according to the attributes of
        this CStrField instance.

        If null_terminated is True, all bytes after the first zero byte are
        ignored.
        """
        if self.null_terminated:
            bs = bs.split(b'\0', 1)[0]

        return bs.decode(self.encoding, self.errors)

    def str_to_bytes(self, s: str) -> bytes:
        """Convert the given string to bytes, according to the attributes of
        this CStrField instance.

        A zero byte is appended to the result if null_terminated is True.
        Raises an IndexError if encoding the string results in a series of
        bytes that is longer than max_length.
        """
        bs = s.encode(self.encoding, self.errors)
        if self.null_terminated:
            bs += b'\0'

        if len(bs) > self.max_length:
            raise IndexError(f'String is {len(bs)} bytes, but the maximum is {self.max_length}')

        return bs


class TypedStructBuilder(Generic[CSU]):
    CSTR_RAW_BYTES_PREFIX: ClassVar[str] = '_raw_'
    ATTR_NAME_BLACKLIST: ClassVar[set[str]] = {'_anonymous_', '_pack_'}

    target_cls: type[CSU]
    hints: dict[str, Any]
    unannotated_hints: dict[str, Any]

    fields: list[CStructureField]

    def __init__(self, target_cls: type[CSU]) -> None:
        self.target_cls = target_cls
        self.hints = typing.get_type_hints(target_cls, include_extras=True)
        self.unannotated_hints = typing.get_type_hints(target_cls, include_extras=False)

    def wrap(self) -> type[CSU]:
        self.fields = []

        if hasattr(self.target_cls, '_fields_'):
            raise TypeError('typed_struct should not be used with classes that already have a '
                            '_fields_ attribute')

        for attr_name, hint in self.hints.items():
            if attr_name in self.ATTR_NAME_BLACKLIST:
                continue

            if self.annotation_isinstance(hint, ClassVar):  # type: ignore[arg-type]
                continue

            unannotated_hint = self.unannotated_hints[attr_name]

            if cfld := self.get_first_annotated_md_of_type(hint, CField):
                self._typecheck_cfield(attr_name, cfld, unannotated_hint)
                self._apply_cfield(attr_name, cfld)
            elif cstr := self.get_first_annotated_md_of_type(hint, CStrField):
                self._typecheck_cstrfield(attr_name, cstr, unannotated_hint)
                self._apply_cstrfield(attr_name, cstr)

        self.target_cls._fields_ = self.fields[:]
        return self.target_cls

    def _typecheck_cfield(self, name: str, cfld: CField, unannotated_hint: Any) -> None:
        if issubclass(cfld.ctype, C.Array) and not self.annotation_is_sequence(unannotated_hint):
            raise TypeError(f'Array CField "{name}" should be an annotated Sequence')

    def _apply_cfield(self, name: str, cfld: CField) -> None:
        if cfld.bitwidth is not None:
            self.fields.append((name, cfld.ctype, cfld.bitwidth))
        else:
            self.fields.append((name, cfld.ctype))

    def _typecheck_cstrfield(self, name: str, cstr: CStrField, unannotated_hint: Any) -> None:
        if not issubclass(unannotated_hint, str):
            raise TypeError(f'CStrField "{name}" should be an annotated str')

    def _apply_cstrfield(self, name: str, cstr: CStrField) -> None:
        field_name = self.CSTR_RAW_BYTES_PREFIX + name
        self.fields.append((field_name, C.c_char * cstr.max_length))

        self._add_string_prop(name, field_name, cstr)

    def _add_string_prop(self, prop_name: str, field_name: str, cstr: CStrField) -> None:
        """Adds a property to transparently read and write a ctypes.c_char
        array as a str.

        Arguments:
        name: The name of the property. The underlying ctypes array is assumed
            to be a prefixed version of this string.
        cstr: The CStrField instance defining the behavior of the string.
        """
        def getter(self: Any) -> str:
            return cstr.bytes_to_str(getattr(self, field_name))

        def setter(self: Any, value: str) -> None:
            setattr(self, field_name, cstr.str_to_bytes(value))

        setattr(self.target_cls, prop_name, property(getter, setter))

    @classmethod
    def annotation_isinstance(cls, note: Any, note_cls: type) -> bool:
        """Checks if a type annotation is an instance of note_cls."""
        # Normal isinstance doesn't work on type annotation classes because of
        # all the crazy trickery used for type checking.
        return typing.get_origin(note) is note_cls

    @classmethod
    def annotation_is_sequence(cls, unannotated_hint: Any) -> bool:
        """Returns true if the given annotation is Sequence, a specialized
        Sequence (e.g. Sequence[int]), or a subclass of Sequence."""
        # A Sequence hint without a type parameter is easy:
        if unannotated_hint is Sequence:
            return True

        # Sequence itself turns into collections.abc.Sequence if you look at it
        # at all. That also happens to be its origin.
        sequence_origin = typing.get_origin(Sequence)
        if sequence_origin is None:
            return False  # shouldn't happen

        # A subclass of Sequence without a parameter will have Sequence's
        # origin in its mro.
        if sequence_origin in unannotated_hint.mro():
            return True

        # A specialized Sequence is actually an instance of a _GenericAlias,
        # and its origin will be Sequence's origin.
        origin = typing.get_origin(unannotated_hint)
        if origin is None:
            return False

        if origin is sequence_origin:
            return True

        # A specialized subclass of Sequence will have Sequence's origin in its
        # mro.
        if sequence_origin in origin.mro():
            return True

        return False

    @classmethod
    def get_first_annotated_md_of_type(cls, note: Any, md_cls: type[T]) -> Optional[T]:
        """If note is an Annotated type annotation, returns the first piece of
        metadata belonging to it that is an instance of md_cls.

        If note is not an Annotated instance, or if it has no such metadata,
        returns None.
        """
        if not cls.annotation_isinstance(note, Annotated):  # type: ignore[arg-type]
            return None

        # The first arg is the underlying type; skip it
        metadata = typing.get_args(note)[1:]
        for md in metadata:
            if isinstance(md, md_cls):
                return md

        return None


def typed_struct(cls: type[CSU]) -> type[CSU]:
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
    return TypedStructBuilder(cls).wrap()

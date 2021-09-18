from typing import Annotated, ClassVar, Optional, Any, Sequence, TypeVar, Union
import typing
import ctypes as C
import sys
from dataclasses import dataclass
from utils import AnyCType

"""
TODO:
- endian-specific AStruct classes?
- less verbose annotations!
- get rid of the FieldsBuilder class? bake it into AStructMeta?
"""

CStructureField = Union[tuple[str, type[AnyCType]], tuple[str, type[AnyCType], int]]
CStructureFields = Sequence[CStructureField]
T = TypeVar('T')
CT = TypeVar('CT', bound=AnyCType)


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
    """
    ctype: type[AnyCType]
    bitwidth: Optional[int] = None


@dataclass(frozen=True)
class CStrField:
    """Annotation metadata for a C-string member of an AStruct class.

    Use by annotating a class attribute in an AStruct like this:
        name: Annotated[str, CStrField(32, encoding='utf-8')]

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


class FieldsBuilder:
    CSTR_RAW_BYTES_PREFIX: ClassVar[str] = '_raw_'

    @classmethod
    def reify_annotation(cls, note: Any, __globals: dict[str, Any]) -> Any:
        """Evaluate a type annotation using the given globals.

        Like a one-shot version of typing.get_type_hints. If the annotation is
        not a string, simply returns it.
        """

        # typing.get_type_hints unfortunately won't work for us because we
        # don't have a class yet.
        # TODO: error handling on this eval?
        if isinstance(note, str):
            return eval(note, __globals)

        return note

    @classmethod
    def annotation_isinstance(cls, note: Any, note_cls: type) -> bool:
        """Checks if a type annotation is an instance of note_cls."""
        # Normal isinstance doesn't work on type annotation classes because of
        # all the crazy trickery used for type checking.
        return typing.get_origin(note) is note_cls

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

    @classmethod
    def get_fields(cls,
                   annotations: dict[str, Any],
                   __globals: dict[str, Any]) -> tuple[CStructureFields, dict[str, CStrField]]:
        """Builds a _fields_ value given a dict of type annotations.

        Arguments:
        annotations: The type annotations for fields on the class in
            consideration (as pulled, e.g., from its __annotations__
            attribute).
        __globals: The dict of globals to use when evaluating the type
            annotations in the first argument.

        Returns a tuple of the _fields_ value and a dict of any CStrField
        attributes, so they may be processed specially. The names of the
        fields returned may not match the names of the attrs in the
        annotations dict. For example, CStrField attributes are given a prefix
        to hide raw access to their underlying bytes.

        Only considers non-ClassVar fields annotated with either CField or
        CStrField. The special ctypes attributes _anonymous_ and _pack_ are
        explicitly skipped.
        """
        NAME_BLACKLIST = {'_anonymous_', '_pack_'}

        fields: list[CStructureField] = []
        cstr_fields: dict[str, CStrField] = {}

        for attr_name, note in annotations.items():
            if attr_name in NAME_BLACKLIST:
                continue

            note = cls.reify_annotation(note, __globals)

            if cls.annotation_isinstance(note, ClassVar):  # type: ignore[arg-type]
                continue

            if cstr := cls.get_first_annotated_md_of_type(note, CStrField):
                field_name = cls.CSTR_RAW_BYTES_PREFIX + attr_name
                fields.append((field_name, C.c_char * cstr.max_length))
                cstr_fields[attr_name] = cstr
            elif cfld := cls.get_first_annotated_md_of_type(note, CField):
                if cfld.bitwidth is not None:
                    fields.append((attr_name, cfld.ctype, cfld.bitwidth))
                else:
                    fields.append((attr_name, cfld.ctype))

        return (fields, cstr_fields)


# mypy doesn't like the dynamic base class; hence the ignore
class AStructMeta(type(C.Structure)):  # type: ignore[misc]
    """Metaclass for AStructs.

    Handles massaging class-level type annotations into the _fields_ class
    attr, before handing the work off to ctypes.Structure's metaclass.

    Also adds transparent str properties for attrs annotated with the CStrField
    metadata.
    """

    @classmethod
    def add_string_prop(cls, target_cls: type, name: str, cstr: CStrField) -> None:
        """Adds a property to transparently read and write a ctypes.c_char
        array as a str.

        Arguments:
        target_cls: The class to which we are adding a property.
        name: The name of the property. The underlying ctypes array is assumed
            to be a prefixed version of this string.
        cstr: The CStrField instance defining the behavior of the string.
        """
        raw_attr = FieldsBuilder.CSTR_RAW_BYTES_PREFIX + name

        def getter(self: Any) -> str:
            return cstr.bytes_to_str(getattr(self, raw_attr))

        def setter(self: Any, value: str) -> None:
            setattr(self, raw_attr, cstr.str_to_bytes(value))

        setattr(target_cls, name, property(getter, setter))

    def __new__(cls, name: str, bases: Any, classdict: dict[str, Any]) -> 'AStructMeta':
        if '_fields_' in classdict:
            raise ValueError('The _fields_ class variable should not be specified for a AStruct')

        cls_globals = vars(sys.modules[cls.__module__])
        notes: dict[str, Any] = classdict.get('__annotations__', {})

        fields, cstr_fields = FieldsBuilder.get_fields(notes, cls_globals)
        if len(fields):
            classdict['_fields_'] = fields

        struct_cls: 'AStructMeta' = super().__new__(cls, name, bases, classdict)  # type: ignore

        # Expose CStrField fields as str properties
        for prop_name, cstr in cstr_fields.items():
            cls.add_string_prop(struct_cls, prop_name, cstr)

        return struct_cls

    # pylance can't really pick up on the existence of these methods because we
    # have a dynamic base class. These passthroughs help it understand.
    # Ignored for typing because we can't express that this metaclass will only
    # be used for ctypes.Structure subclasses.
    def __mul__(cls: type[CT], other: int) -> type[C.Array[CT]]:  # type: ignore
        return super().__mul__(other)  # type: ignore

    def __rmul__(cls: type[CT], other: int) -> type[C.Array[CT]]:  # type: ignore
        return super().__rmul__(other)  # type: ignore


class AStruct(C.Structure, metaclass=AStructMeta):
    """A wrapper to allow declaring ctypes.Structure subclasses with type
    annotations instead of _fields_.

    To use, create a subclass and add describe your fields with class-level
    attributes, annotated with either CField or CStrField. AStruct generates
    transparent string properties for fixed-length c_char arrays via the
    CStrField metadata.

    An example:

    class Player(AStruct):
        level: Annotated[int, CField(c_uint16)]
        hp: Annotated[int, CField(c_uint16)]
        skill_aptitudes: Annotated[Sequence[int], CField(c_uint8 * 8)]
        name: Annotated[str, CStrField(16)]

    Further subclassing and the standard _pack_ attribute work as they do with
    normal ctype.Structure subclasses. You can nest an AStruct in the _fields_
    of another ctype.Structure or via a type annotation in another AStruct. You
    are also free to add instance and class methods to your AStruct subclasses.
    """
    pass


class PackedAStruct(AStruct):
    """An AStruct with _pack_ = 1."""
    _pack_: ClassVar[int] = 1

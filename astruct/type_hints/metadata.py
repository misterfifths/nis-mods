from typing import Optional
from dataclasses import dataclass
from .ctypes_aliases import AnyCType


@dataclass(frozen=True)
class CField:
    """Annotation metadata for a field of an typed_struct class.

    Use by annotating a class attribute in an typed_struct like this:
        level: Annotated[int, CField(c_uint32)]

    Note that there are predefined aliases for this sort of annotation for all
    the built-in ctypes in the type_hints module. For example, the above is
    exactly equivalent to
        level: CUInt32

    For arrays of c_chars that represent fixed-length strings, consider using
    the CStr or CWStr types.

    For other kinds of C arrays, consider the helpers in the type_hints module,
    or an annotated CArray type hint.

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


class NotNullTerminated:
    """Annotation metadata to indicate a CStr or CWStr is not null-terminated.

    Example of an annotated attribute in a typed_struct:
        s: Annotated[CStr[10], NotNullTerminated()]

    By default, null termination is enforced on CStr and CWStr fields. This
    metadata turns off that behavior.
    """
    pass


@dataclass(frozen=True)
class Encoding:
    """Annotation metadata to control the encoding of a CStr or CWStr.

    Example of an annotated attribute in a typed_struct:
        s: Annotated[CStr[10], Encoding('utf-8', errors='replace')]

    The default for an unannotated CStr or CWStr is the shift-jis encoding with
    strict error handling. Providing this metadata allows control over that
    behavior.

    Attributes:
    encoding: The encoding of the string. Default: 'shift-jis'.
    errors: What to do if an error is encountered in en/decoding the string.
    One of the constants from bytes.decode. Default: 'strict'.
    """
    encoding: str = 'shift-jis'
    errors: str = 'strict'


@dataclass(frozen=True)
class Length:
    """Annotation metadata to control the length of a CArray.

    Example of an annotated attribute in a typed_struct:
        s: Annotated[CArray[SomeOtherStruct], Length(10)]

    This annotation is only necessary when representing a C array of a struct
    or union. For arrays of float- or int-compatible ctypes, the helper types
    in the type_hints module are much more convenient.
    """
    length: int

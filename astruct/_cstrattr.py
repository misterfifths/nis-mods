from typing import Any, ClassVar, Optional, Union
import typing
import ctypes as C
from dataclasses import dataclass
from ._type_hint_utils import hint_is, first_annotated_md_of_type
from .type_hints.ctypes_aliases import AnyCType
from .type_hints.metadata import Encoding, NotNullTerminated
from .type_hints.cstr import CStr, CWStr


@dataclass
class CStrAttr:
    """Represents the configuration of a CStr or CWStr attribute on a
    typed_struct."""
    RAW_FIELD_PREFIX: ClassVar[str] = '_raw_'  # TODO: @dataclass + Final = sad

    raw_field_name: str
    max_length: int
    ctype: Union[type[C.c_char], type[C.c_wchar]]
    encoding: str = 'shift-jis'
    errors: str = 'strict'
    null_terminated: bool = True

    @classmethod
    def _from_type_hint(cls,
                        attr_name: str,
                        hint: Any,
                        unannotated_hint: Any) -> Optional['CStrAttr']:
        """Constructs an instance from the given type hint if possible.

        Retrieves relevant metadata (e.g. Encoding) from the hint if it is
        Annotated.

        If the hint is not for CStr, CWStr, or an Annotated version thereof,
        returns None.
        """
        if hint_is(unannotated_hint, CStr):
            ctype = C.c_char
        elif hint_is(unannotated_hint, CWStr):
            ctype = C.c_wchar
        else:
            return None

        max_length = typing.get_args(unannotated_hint)[0]
        res = cls(cls.RAW_FIELD_PREFIX + attr_name, max_length, ctype)

        if encoding_md := first_annotated_md_of_type(hint, Encoding):
            res.encoding = encoding_md.encoding
            res.errors = encoding_md.errors

        if first_annotated_md_of_type(hint, NotNullTerminated):
            res.null_terminated = False

        return res

    def bytes_to_str(self, bs: bytes) -> str:
        """Convert the given bytes to a string, according to the attributes of
        this instance.

        If null_terminated is True, all bytes after the first zero byte are
        ignored.
        """
        if self.null_terminated:
            bs = bs.split(b'\0', 1)[0]

        return bs.decode(self.encoding, self.errors)

    def str_to_bytes(self, s: str) -> bytes:
        """Convert the given string to bytes, according to the attributes of
        this instance.

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

    def __get__(self, instance: AnyCType, owner: Any = None) -> str:
        raw_val: bytes = getattr(instance, self.raw_field_name)
        return self.bytes_to_str(raw_val)

    def __set__(self, instance: AnyCType, value: str) -> None:
        bs = self.str_to_bytes(value)
        setattr(instance, self.raw_field_name, bs)

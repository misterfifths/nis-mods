from typing import Any, Optional
import typing
from dataclasses import dataclass
from ._type_hint_utils import hint_is, first_annotated_md_of_type
from .type_hints.metadata import Encoding, NotNullTerminated
from .type_hints.cstr import CStr, CWStr


@dataclass
class CStrAttr:
    """Represents the configuration of a CStr or CWStr attribute on a
    typed_struct."""
    max_length: int
    encoding: str = 'shift-jis'
    errors: str = 'strict'
    null_terminated: bool = True

    @classmethod
    def _is_cstr_hint(cls, hint: Any, unannotated_hint: Any) -> bool:
        return hint_is(unannotated_hint, CStr) or hint_is(unannotated_hint, CWStr)

    @classmethod
    def from_type_hint(cls, hint: Any, unannotated_hint: Any) -> Optional['CStrAttr']:
        """Constructs an instance from the given type hint if possible.

        Retrieves relevant metadata (e.g. Encoding) from the hint if it is
        Annotated.

        If the hint is not for CStr, CWStr, or an Annotated version thereof,
        returns None.
        """
        if not cls._is_cstr_hint(hint, unannotated_hint):
            return None

        max_length = typing.get_args(unannotated_hint)[0]
        res = cls(max_length)

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

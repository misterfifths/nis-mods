from typing import Any, ClassVar, Optional
import typing
import ctypes as C
import codecs
from dataclasses import dataclass
from ._type_hint_utils import hint_is_specialized, first_annotated_md_of_type
from .ctypes_utils import get_bytes_for_field, set_bytes_for_field
from .type_hints.extras import CStructureOrUnion
from .type_hints.metadata import DoNotZeroExtraBytes, Encoding, NotNullTerminated
from .type_hints.cstr import CStr


"""
Arrays of c_char and c_wchar do some very strange things when it come to null-
termination.

Setting a c_char array field silently null-terminates the value you set if it
can, but doesn't if it won't fit. E.g., say you have a field x of type
c_char * 5. If you do x = b'ab', it will set the first three bytes in the
underlying buffer to 'ab\0' and leave the remaining bytes alone. If you do
x = b'abcde', it won't complain but won't add a zero (because there's no room).

Setting a c_char array will also treat the incoming bytes as null-terminated.
If you do x = b'ab\0de', everything after the zero is ignored and the
corresponding bytes are untouched in the underlying buffer. The same goes for
something like b'a\0\0\0\0'; only the first null byte is written.

Reading back a c_char array as bytes will stop at the first null byte.

c_wchar arrays are different still! If the string you're setting is shorter
than the length of the field, it adds a null byte. But unlike when setting a
c_char array, it won't stop after the first null character in the input string,
so setting s = 'x\0ab' on a c_wchar array *will* actually put in the "a" and
"b".

Reading back a c_wchar array as a string will include all bytes in the
underlying buffer.

Long story short: ignoring the c_char and c_wchar types is our best bet.
Instead we'll use byte arrays and manually encode/decode strings, and memmove
bytes into place when needed.
"""


@dataclass
class CStrAttr:
    """Represents the configuration of a CStr attribute on a typed_struct."""
    RAW_FIELD_PREFIX: ClassVar[str] = '_raw_'  # TODO: @dataclass + Final = sad

    attr_name: str
    raw_field_name: str
    byte_length: int
    array_ctype: type[C.Array[C.c_uint8]]  # see note above about c_char
    encoding: str = 'shift-jis'
    errors: str = 'strict'
    element_ctype: type[C.c_uint8] = C.c_uint8
    null_terminated: bool = True
    zero_extra_bytes: bool = True
    _incremental_decoder: Optional[codecs.IncrementalDecoder] = None

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
        # Catch CStr without a length
        if unannotated_hint is CStr:
            raise TypeError('CStr requires a single, positive integer length argument')

        if not hint_is_specialized(unannotated_hint, CStr):
            # Not ours to handle
            return None

        byte_length = typing.get_args(unannotated_hint)[0]

        if not isinstance(byte_length, int) or byte_length <= 0:
            raise TypeError('CStr requires a single, positive integer length argument')

        res = cls(attr_name,
                  cls.RAW_FIELD_PREFIX + attr_name,
                  byte_length,
                  C.c_uint8 * byte_length)

        if encoding_md := first_annotated_md_of_type(hint, Encoding):
            res.encoding = encoding_md.encoding
            res.errors = encoding_md.errors

        if first_annotated_md_of_type(hint, NotNullTerminated):
            res.null_terminated = False

        if res.null_terminated:
            # We only need this for null-terminated strings
            res._incremental_decoder = codecs.getincrementaldecoder(res.encoding)(res.errors)

        if first_annotated_md_of_type(hint, DoNotZeroExtraBytes):
            res.zero_extra_bytes = False

        return res

    def _decode_null_terminated(self, bs: bytes) -> str:
        """Decodes up to the first null character in the given bytes and
        returns the result (without the null). Does not consider attempt to
        decode any bytes after the first null character.

        If errors is 'strict', raises a ValueError if no null character is
        decoded from the bytes.
        """
        assert self._incremental_decoder

        res = ''
        one_byte = bytearray(1)  # avoiding some churn
        for i, b in enumerate(bs):
            final = i == len(bs) - 1
            one_byte[0] = b

            # decode() returns '' if the input was ok but incomplete, a
            # character if it has decoded something, or raises an error if
            # the byte moved us to an invalid state.
            if c := self._incremental_decoder.decode(one_byte, final):
                if c == '\0':
                    # We're done!
                    return res

                res += c

        # We didn't hit a null.
        if self.errors == 'strict':
            raise ValueError('Missing null terminator in string')

        return res

    def bytes_to_str(self, bs: bytes) -> str:
        """Convert the given bytes to a string, according to the attributes of
        this instance.

        If null_terminated is True, all bytes after the first decoded zero
        character are ignored. If null_terminated is True and errors is
        'strict', a ValueError is raised if no zero character is decoded.
        """
        if self.null_terminated:
            return self._decode_null_terminated(bs)

        return bs.decode(self.encoding, self.errors)

    def str_to_bytes(self, s: str) -> bytes:
        """Convert the given string to bytes, according to the attributes of
        this instance.

        If null_terminated is True, a zero character is appended to the input
        (if needed) before encoding.

        Raises an IndexError if encoding the string results in a series of
        bytes that is longer than byte_length.
        """
        if self.null_terminated and not s.endswith('\0'):
            s += '\0'

        bs = s.encode(self.encoding, self.errors)

        if len(bs) > self.byte_length:
            raise IndexError(f'String is {len(bs)} bytes, but the maximum is {self.byte_length}')

        if self.zero_extra_bytes and len(bs) < self.byte_length:
            # Zero pad to the full length of the field
            bs += b'\0' * (self.byte_length - len(bs))

        return bs

    def __get__(self, instance: CStructureOrUnion, owner: Any = None) -> str:
        # See the note at the top of the file about why we manipulate bytes
        # directly.
        raw_val = get_bytes_for_field(instance, self.raw_field_name)
        try:
            return self.bytes_to_str(raw_val)
        except ValueError as e:
            raise ValueError(f'Missing null terminator for field "{self.attr_name}"') from e

    def __set__(self, instance: CStructureOrUnion, value: str) -> None:
        # See the note at the top of the file about why we manipulate bytes
        # directly.
        bs = self.str_to_bytes(value)
        set_bytes_for_field(instance, self.raw_field_name, bs)

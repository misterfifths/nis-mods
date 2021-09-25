from typing import Any, ClassVar, Optional
import typing
import ctypes as C
import codecs
from dataclasses import dataclass
from ._type_hint_utils import hint_is_specialized, first_annotated_md_of_type
from .ctypes_utils import get_bytes_for_field, set_bytes_for_field
from .type_hints.ctypes_aliases import CharCType
from .type_hints.extras import CStructureOrUnion
from .type_hints.metadata import DoNotZeroExtraBytes, Encoding, NotNullTerminated
from .type_hints.cstr import CStr, CWStr


@dataclass
class CStrAttr:
    """Represents the configuration of a CStr or CWStr attribute on a
    typed_struct."""
    RAW_FIELD_PREFIX: ClassVar[str] = '_raw_'  # TODO: @dataclass + Final = sad

    attr_name: str
    raw_field_name: str
    max_length: int
    element_ctype: type[CharCType]
    array_ctype: type[C.Array[CharCType]]
    encoding: str = 'shift-jis'
    errors: str = 'strict'
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
        ctype: type[CharCType]
        if hint_is_specialized(unannotated_hint, CStr):
            ctype = C.c_char
        elif hint_is_specialized(unannotated_hint, CWStr):
            ctype = C.c_wchar
        else:
            return None

        max_length = typing.get_args(unannotated_hint)[0]
        res = cls(attr_name,
                  cls.RAW_FIELD_PREFIX + attr_name,
                  max_length,
                  ctype,
                  ctype * max_length)

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
        bytes that is longer than max_length.
        """
        if self.null_terminated and not s.endswith('\0'):
            s += '\0'

        bs = s.encode(self.encoding, self.errors)

        if len(bs) > self.max_length:
            raise IndexError(f'String is {len(bs)} bytes, but the maximum is {self.max_length}')

        if self.zero_extra_bytes and len(bs) < self.max_length:
            # Zero pad to the full length of the field
            bs += b'\0' * (self.max_length - len(bs))

        return bs

    def __get__(self, instance: CStructureOrUnion, owner: Any = None) -> str:
        # See the note below; getting the attr for c_char arrays is weird and
        # enforces null termination, so we need to fetch the raw bytes here.
        raw_val = get_bytes_for_field(instance, self.raw_field_name)
        try:
            return self.bytes_to_str(raw_val)
        except ValueError as e:
            raise ValueError(f'Missing null terminator for field "{self.attr_name}"') from e

    def __set__(self, instance: CStructureOrUnion, value: str) -> None:
        # Directly setting ctypes arrays of c_chars acts really weird. It
        # effectively silently null-terminates the value you set if it can, but
        # doesn't if it won't fit. E.g., say you have a field x of type
        # c_char * 5. If you do x = b'ab', it will set the first three bytes
        # in the underlying buffer to 'ab\0' and leave the remaining bytes
        # alone. If you do x = b'abcde', it won't complain but won't add a
        # zero (because there's no room).
        # It will also treat the incoming data as null-terminated. If you do
        # x = b'ab\0de', everything after the zero is ignored and the
        # corresponding bytes are untouched in the underlying buffer. The same
        # goes for something like b'a\0\0\0\0'. So the best way for us to get
        # the behavior we want is to manually memmove the bytes in here.
        # str_to_bytes generates what we actually want the final bytes in the
        # buffer to be, and we just copy it into place.
        bs = self.str_to_bytes(value)
        set_bytes_for_field(instance, self.raw_field_name, bs)

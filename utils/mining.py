import inspect
from typing import Iterable

from astruct._cstrattr import CStrAttr
from astruct.ctypes_utils import get_bytes_for_field
from astruct.str_utils import NullTerminationError, decode_null_terminated, get_incremental_decoder
from astruct.type_hints import *

from .hexdump import hexdump

__all__ = ['all_zero', 'unkdump', 'check_zero_fields', 'iter_cstr_fields',
           'check_null_terminated_strs']


def all_zero(xs: Iterable[int]) -> bool:
    """Returns True if all the elements of the argument are zero."""
    return all(x == 0 for x in xs)


def unkdump(s: CStructureOrUnion, encoding: str = 'shift-jis', decimal: bool = False) -> None:
    """Hexdumps all the fields of the given ctypes Structure whose names begin
    with '_unk'.

    Uses the given encoding for the character interpretation in the hex dump.
    """
    fields: CStructureFields = s._fields_
    for tup in fields:
        name = tup[0]
        if not name.startswith('_unk'):
            continue

        bs = get_bytes_for_field(s, name)
        print(f'==> {name}')
        hexdump(bs, encoding=encoding, decimal=decimal)


def check_zero_fields(s: CStructureOrUnion, encoding: str = 'shift-jis') -> None:
    """Checks that the bytes for fields with a name beginning with '_zero' are
    all actually zero, and hexdumps any that aren't.

    Uses the given encoding for the character interpretation in the hex dump.
    """
    fields: CStructureFields = s._fields_
    for tup in fields:
        name = tup[0]
        if not name.startswith('_zero'):
            continue

        bs = get_bytes_for_field(s, name)
        if not all_zero(bs):
            print(f'Field {name} is not all zeroes!')
            hexdump(bs, encoding=encoding)


def iter_cstr_fields(s: CStructureOrUnion) -> Iterable[tuple[str, CStrAttr]]:
    """Iterates the names and attributes of the CStr fields of the given ctypes
    Structure (which is presumably a typed_struct)."""
    for name, desc in inspect.getmembers(type(s), inspect.isdatadescriptor):
        if isinstance(desc, CStrAttr):
            yield (name, desc)


def check_null_terminated_strs(s: CStructureOrUnion, check_zeroes_after_null: bool = True) -> None:
    """Checks that all the CStr fields of the given ctypes Structure are
    properly null terminated and, optionally, that all the bytes after the null
    are zero.

    Hexdumps any strings that do not comply, using their own specified
    encoding. Ignores any CStrs with the NotNullTerminated metadata.
    """
    for name, cstrattr in iter_cstr_fields(s):
        if not cstrattr.null_terminated:
            continue

        decoder = get_incremental_decoder(cstrattr.encoding, cstrattr.errors)
        bs = get_bytes_for_field(s, cstrattr.raw_field_name)
        null_missing = False
        str_byte_len = -1
        try:
            _, str_byte_len = decode_null_terminated(bs, decoder, ignore_missing=False)
        except NullTerminationError:
            null_missing = True

        # null_missing implies we went all the way through the bytes in the
        # string, so these cases are mutually exclusive.
        if null_missing:
            print(f'String field {name} is missing its null terminator')
            hexdump(bs, encoding=cstrattr.encoding)
        elif check_zeroes_after_null:
            bytes_after_null = bs[str_byte_len:]
            if not all_zero(bytes_after_null):
                print(f'String field {name} has non-zero bytes after null')
                hexdump(bs, encoding=cstrattr.encoding)

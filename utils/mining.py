import inspect
from collections import defaultdict
from typing import Callable, Iterable, Optional, TypeVar

from astruct._cstrattr import CStrAttr
from astruct.ctypes_utils import get_bytes_for_field
from astruct.str_utils import NullTerminationError, decode_null_terminated, get_incremental_decoder
from astruct.type_hints import *

from .hexdump import hexdump

__all__ = ['all_zero', 'unkdump', 'check_zero_fields', 'iter_cstr_fields',
           'max_length_of_str_field', 'check_null_terminated_strs',
           'check_str_field_padding', 'group_and_dump']

T = TypeVar('T', bound=CStructureOrUnion)
K = TypeVar('K')


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


def max_length_of_str_field(ss: Iterable[T], field_name: str) -> tuple[int, T]:
    """Iterates the objects in ss, returning a tuple of longest byte length of
    the given string field and the object containing it.

    String decoding stops at the first zero character. Raises an error if
    field_name is not a CStr field, or if ss is empty.
    """
    raw_field_name = None
    decoder = None

    max_len = -1
    src_obj: Optional[T] = None

    for s in ss:
        if raw_field_name is None:
            for str_field_name, cstrattr in iter_cstr_fields(s):
                if str_field_name == field_name:
                    raw_field_name = cstrattr.raw_field_name
                    decoder = get_incremental_decoder(cstrattr.encoding, cstrattr.errors)
                    break

            if raw_field_name is None:
                raise ValueError(f'field {field_name!r} is not a CStr')

        assert decoder  # for type-checking

        bs = get_bytes_for_field(s, raw_field_name)
        _, byte_len = decode_null_terminated(bs, decoder, ignore_missing=True)

        if byte_len > max_len:
            max_len = byte_len
            src_obj = s

    if src_obj is None:
        raise IndexError('iterable is empty')

    return (max_len, src_obj)


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


def check_str_field_padding(s: T, strify_struct: Callable[[T], str]) -> None:
    """Checks for CStr fields on s that end in whitespace (ASCII space, tab,
    or newline, or U+3000 Ideographic Space).

    If any field is found, its name and value is printed, with the header
    returned by strify_struct.
    """
    printed_desc = False
    for name, _ in iter_cstr_fields(s):
        val: str = getattr(s, name)
        if val.endswith(' \t\n\u3000'):
            if not printed_desc:
                print(strify_struct(s))
                printed_desc = True
            print(f'  field {name} has trailing padding: {val!r}')

    if printed_desc:
        print()


def group_and_dump(objects: Iterable[T],
                   key: Callable[[T], K],
                   only_show_non_unique: bool = False,
                   strify_obj: Callable[[T], str] = repr,
                   strify_key: Callable[[K], str] = repr) -> None:
    """Groups objects by the given key and prints a description of each group.

    The given strify functions will be used to generate string versions of the
    objects and keys, respectively. If only_show_non_unique is True, only keys
    with more than one corresponding object will be printed.
    """
    objs_by_key: defaultdict[K, list[T]] = defaultdict(list)
    for obj in objects:
        objs_by_key[key(obj)].append(obj)

    first = True
    for k, objs in objs_by_key.items():
        if only_show_non_unique and len(objs) == 1:
            continue

        if not first:
            print()
        first = False

        print(f'Value {strify_key(k)} - {len(objs)} objects:')
        for obj in objs:
            print(f'  {strify_obj(obj)}')

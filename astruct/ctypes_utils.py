import ctypes as C

from .type_hints.extras import CStructureOrUnion


def get_bytes_for_field(s: CStructureOrUnion, field_name: str) -> bytes:
    """Returns a copy of the bytes that represent the given field of a ctypes
    Structure or Union."""
    desc = getattr(type(s), field_name)
    offset = desc.offset
    size = desc.size

    buf = C.create_string_buffer(size)
    C.memmove(buf, C.byref(s, offset), size)

    return bytes(buf)


def set_bytes_for_field(s: CStructureOrUnion, field_name: str, bs: bytes) -> None:
    """Sets the underlying bytes for a given field of a ctypes Structure or
    Union.

    An IndexError is raised if bs is not of a length less than or equal to the
    byte size of the field.
    """
    desc = getattr(type(s), field_name)
    offset = desc.offset
    size = desc.size

    if len(bs) > size:
        raise IndexError(f'Got {len(bs)} bytes, but field {field_name!r} is only {size} bytes')

    src_buf = C.c_buffer(bs)
    C.memmove(C.byref(s, offset), src_buf, len(bs))

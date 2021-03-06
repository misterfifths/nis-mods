from typing import TYPE_CHECKING, ByteString, Iterable, Union

if TYPE_CHECKING:
    import mmap

BytesLike = Union[ByteString, memoryview, 'mmap.mmap']


def hexlify(bs: Union[BytesLike, Iterable[int], int]) -> str:
    """Converts each byte in the argument into the corresponding 2-digit hex
    representation, and returns them all joined with spaces.

    No attempt is made to ensure that elements in the argument are between 0
    and 255. If one is outside of that range, its corresponding substring in
    the return may be longer than 2 hexadecimal digits.
    """
    if isinstance(bs, int):
        return f'{bs:02x}'

    return ' '.join(f'{b:02x}' for b in bs)  # type: ignore


def build_bytes(*parts: Union[str, BytesLike, int, Iterable[int]],
                encoding: str = 'utf8',
                errors: str = 'strict') -> bytearray:
    """Constructs a single bytearray by concatenating a mixture of bytes, ints,
    Iterables of ints, and/or strings. Strings are decoded into bytes with the
    given encoding.

    Any integer arguments must be between 0 and 255, inclusive.
    """
    res = bytearray()
    for part in parts:
        if isinstance(part, bytes):
            res.extend(part)
        elif isinstance(part, str):
            bs = part.encode(encoding, errors=errors)
            res.extend(bs)
        elif isinstance(part, int):
            res.append(part)
        else:
            res.extend(part)  # type: ignore

    return res

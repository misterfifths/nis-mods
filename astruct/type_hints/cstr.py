import typing
from types import GenericAlias
from typing import Any, Optional

"""
We want to be able to type-hint fixed-length C strings on classes like this:
    name: CStr[10]

But even if CStr is a str subclass, we can't do something simple like
    x.name = 'Joan'
because assigning a str to a subclass of it isn't valid.

Our mypy plugin works around this by resolving CStr to str. But for pylance/
pyright, we have to get a little more creative. We trick it with the
conditional __get__ and __set__ methods below that make CStr look like a
descriptor for a str property.

TODO: we should unify this with CStrAttr, which is actually a descriptor.
"""


class CStr(str):
    """Type that transparently represents a fixed-length C string in a
    typed_struct as a str.

    Use by annotating a class attribute in an typed_struct like this (where
    32 is the number of bytes allowed for this string, including the null):
        name: CStr[32]

    NB: the length in brackets is the number of *bytes* in the structure that
    are available for the field, not the number of characters in the resulting
    string. For multibyte encodings, that is a big difference!

    The resulting attribute will transparently convert between bytes and str
    using a particular encoding and optionally enforcing null-termination.
    Attempts to set the attribute to a string that is too long will result in
    an IndexError.

    The default encoding is shift-jis with strict error handling. That can be
    adjusted by applying the Encoding metadata with typing.Annotated.

    Due to the machine-dependent and generally weird semantics of c_wchar, it's
    recommended to only use CStr for strings, even if they're represented in
    memory by 32-bit integers. For example, for a field of 10 little-endian
    UTF-32 chars (= 4 * 10 bytes), use a type hint like this:
        x: Annotated[CStr[40], Encoding('utf-32-le')]

    By default, null-termination of the string is enforced. A zero character
    will be appended to the string (if needed) before it is converted to bytes,
    and everything after the first zero will be ignored when converting to a
    string. This behavior can be turned off by applying the NotNullTerminated
    metadata with typing.Annotated.

    NB: the null-termination behavior appends a zero character to the string
    *before* encoding to bytes. Depending on the encoding, that character may
    need to be represented by more than one byte when stored in the underlying
    buffer. For example, assigning a CStr field with UTF-16-LE encoding the
    value 'ab' will result in trying to store the bytes 'a\\0b\\0\\0\\0'.

    A fully-annotated attribute might look like this:
        name: Annotated[CStr[32],
                        NotNullTerminated(),
                        Encoding('utf-8', errors='replace')]
    """
    def __class_getitem__(cls, params: Any) -> GenericAlias:
        if not isinstance(params, int):
            raise TypeError('Expected a single integer as a type parameter')

        return GenericAlias(cls, params)

    # See the note at the top of the file about this hack.
    if typing.TYPE_CHECKING:
        def __get__(self, obj: Any, type: Optional[type] = None) -> str:
            ...

        def __set__(self, obj: Any, value: str) -> None:
            ...

from typing import Any
from types import GenericAlias

"""
We want to be able to type-hint fixed-length C strings on classes like this:
    name: CStr[10]

In order for that to work in a useful way, CStr needs to be a st subclass.
But if it's an actual subclass, we can't do something simple like
    x.name = 'Joan'
because assigning a str to a subclass isn't valid.

So the hacky solution is this: CStr and CWStr in this module are subclasses of
str with __class_getitem__. (Honestly they probably don't even need to be
str subclasses, but it can't hurt in case someone tries to create an instance.)

We trick the type system with a stub for this file (the .pyi) that makes CStr
and CWStr act like property descriptors, with __get__ and __set__ for str. With
that, everybody's happy!
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

    This class uses ctypes.c_char as the underlying representation. If you
    need ctypes.c_wchar, use CWStr.
    """
    def __class_getitem__(cls, params: Any) -> GenericAlias:
        if not isinstance(params, int):
            raise TypeError('Expected a single integer as a type parameter')

        return GenericAlias(cls, params)


class CWStr(str):
    """A version of CStr represented by ctypes.c_wchar instead of c_char."""
    def __class_getitem__(cls, params: Any) -> GenericAlias:
        if not isinstance(params, int):
            raise TypeError('Expected a single integer as a type parameter')

        return GenericAlias(cls, params)

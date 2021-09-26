# This file is generated by _gen_ctypes_info.py

from typing import Annotated, Any, ClassVar
import ctypes as C
from .carray import CArray
from .metadata import CField, Length

__all__ = ['CBool', 'CByte', 'CInt', 'CInt16', 'CInt32', 'CInt64', 'CInt8', 'CLong', 'CLongLong',
           'CShort', 'CSizeT', 'CSSizeT', 'CUByte', 'CUInt', 'CUInt16', 'CUInt32', 'CUInt64',
           'CUInt8', 'CULong', 'CULongLong', 'CUShort', 'CDouble', 'CFloat', 'CLongDouble',
           'CBoolArray', 'CByteArray', 'CIntArray', 'CInt16Array', 'CInt32Array', 'CInt64Array',
           'CInt8Array', 'CLongArray', 'CLongLongArray', 'CShortArray', 'CSizeTArray',
           'CSSizeTArray', 'CUByteArray', 'CUIntArray', 'CUInt16Array', 'CUInt32Array',
           'CUInt64Array', 'CUInt8Array', 'CULongArray', 'CULongLongArray', 'CUShortArray',
           'CDoubleArray', 'CFloatArray', 'CLongDoubleArray']

# Annotated bool type
CBool = Annotated[bool, CField(C.c_bool)]


# Annotated int types
CByte = Annotated[int, CField(C.c_byte)]
CInt = Annotated[int, CField(C.c_int)]
CInt16 = Annotated[int, CField(C.c_int16)]
CInt32 = Annotated[int, CField(C.c_int32)]
CInt64 = Annotated[int, CField(C.c_int64)]
CInt8 = Annotated[int, CField(C.c_int8)]
CLong = Annotated[int, CField(C.c_long)]
CLongLong = Annotated[int, CField(C.c_longlong)]
CShort = Annotated[int, CField(C.c_short)]
CSizeT = Annotated[int, CField(C.c_size_t)]
CSSizeT = Annotated[int, CField(C.c_ssize_t)]
CUByte = Annotated[int, CField(C.c_ubyte)]
CUInt = Annotated[int, CField(C.c_uint)]
CUInt16 = Annotated[int, CField(C.c_uint16)]
CUInt32 = Annotated[int, CField(C.c_uint32)]
CUInt64 = Annotated[int, CField(C.c_uint64)]
CUInt8 = Annotated[int, CField(C.c_uint8)]
CULong = Annotated[int, CField(C.c_ulong)]
CULongLong = Annotated[int, CField(C.c_ulonglong)]
CUShort = Annotated[int, CField(C.c_ushort)]


# Annotated float types
CDouble = Annotated[float, CField(C.c_double)]
CFloat = Annotated[float, CField(C.c_float)]
CLongDouble = Annotated[float, CField(C.c_longdouble)]


# Array helpers
def _shared_class_getitem(cls: type[CArray[Any, Any]], params: Any) -> Any:
    if not isinstance(params, int) or params <= 0:
        raise TypeError(f'{cls.__name__} requires a single, positive integer length argument')

    # The generic base class with its type arguments is in __orig_bases__
    carray_base = cls.__orig_bases__[0]  # type: ignore
    return Annotated[carray_base, Length(params)]  # type: ignore


# bool array
class CBoolArray(CArray[bool, C.c_bool]):
    _type_: ClassVar[type[C.c_bool]] = C.c_bool

    def __class_getitem__(cls, params: Any) -> Any:
        return _shared_class_getitem(cls, params)


# int arrays
class CByteArray(CArray[int, C.c_byte]):
    _type_: ClassVar[type[C.c_byte]] = C.c_byte

    def __class_getitem__(cls, params: Any) -> Any:
        return _shared_class_getitem(cls, params)


class CIntArray(CArray[int, C.c_int]):
    _type_: ClassVar[type[C.c_int]] = C.c_int

    def __class_getitem__(cls, params: Any) -> Any:
        return _shared_class_getitem(cls, params)


class CInt16Array(CArray[int, C.c_int16]):
    _type_: ClassVar[type[C.c_int16]] = C.c_int16

    def __class_getitem__(cls, params: Any) -> Any:
        return _shared_class_getitem(cls, params)


class CInt32Array(CArray[int, C.c_int32]):
    _type_: ClassVar[type[C.c_int32]] = C.c_int32

    def __class_getitem__(cls, params: Any) -> Any:
        return _shared_class_getitem(cls, params)


class CInt64Array(CArray[int, C.c_int64]):
    _type_: ClassVar[type[C.c_int64]] = C.c_int64

    def __class_getitem__(cls, params: Any) -> Any:
        return _shared_class_getitem(cls, params)


class CInt8Array(CArray[int, C.c_int8]):
    _type_: ClassVar[type[C.c_int8]] = C.c_int8

    def __class_getitem__(cls, params: Any) -> Any:
        return _shared_class_getitem(cls, params)


class CLongArray(CArray[int, C.c_long]):
    _type_: ClassVar[type[C.c_long]] = C.c_long

    def __class_getitem__(cls, params: Any) -> Any:
        return _shared_class_getitem(cls, params)


class CLongLongArray(CArray[int, C.c_longlong]):
    _type_: ClassVar[type[C.c_longlong]] = C.c_longlong

    def __class_getitem__(cls, params: Any) -> Any:
        return _shared_class_getitem(cls, params)


class CShortArray(CArray[int, C.c_short]):
    _type_: ClassVar[type[C.c_short]] = C.c_short

    def __class_getitem__(cls, params: Any) -> Any:
        return _shared_class_getitem(cls, params)


class CSizeTArray(CArray[int, C.c_size_t]):
    _type_: ClassVar[type[C.c_size_t]] = C.c_size_t

    def __class_getitem__(cls, params: Any) -> Any:
        return _shared_class_getitem(cls, params)


class CSSizeTArray(CArray[int, C.c_ssize_t]):
    _type_: ClassVar[type[C.c_ssize_t]] = C.c_ssize_t

    def __class_getitem__(cls, params: Any) -> Any:
        return _shared_class_getitem(cls, params)


class CUByteArray(CArray[int, C.c_ubyte]):
    _type_: ClassVar[type[C.c_ubyte]] = C.c_ubyte

    def __class_getitem__(cls, params: Any) -> Any:
        return _shared_class_getitem(cls, params)


class CUIntArray(CArray[int, C.c_uint]):
    _type_: ClassVar[type[C.c_uint]] = C.c_uint

    def __class_getitem__(cls, params: Any) -> Any:
        return _shared_class_getitem(cls, params)


class CUInt16Array(CArray[int, C.c_uint16]):
    _type_: ClassVar[type[C.c_uint16]] = C.c_uint16

    def __class_getitem__(cls, params: Any) -> Any:
        return _shared_class_getitem(cls, params)


class CUInt32Array(CArray[int, C.c_uint32]):
    _type_: ClassVar[type[C.c_uint32]] = C.c_uint32

    def __class_getitem__(cls, params: Any) -> Any:
        return _shared_class_getitem(cls, params)


class CUInt64Array(CArray[int, C.c_uint64]):
    _type_: ClassVar[type[C.c_uint64]] = C.c_uint64

    def __class_getitem__(cls, params: Any) -> Any:
        return _shared_class_getitem(cls, params)


class CUInt8Array(CArray[int, C.c_uint8]):
    _type_: ClassVar[type[C.c_uint8]] = C.c_uint8

    def __class_getitem__(cls, params: Any) -> Any:
        return _shared_class_getitem(cls, params)


class CULongArray(CArray[int, C.c_ulong]):
    _type_: ClassVar[type[C.c_ulong]] = C.c_ulong

    def __class_getitem__(cls, params: Any) -> Any:
        return _shared_class_getitem(cls, params)


class CULongLongArray(CArray[int, C.c_ulonglong]):
    _type_: ClassVar[type[C.c_ulonglong]] = C.c_ulonglong

    def __class_getitem__(cls, params: Any) -> Any:
        return _shared_class_getitem(cls, params)


class CUShortArray(CArray[int, C.c_ushort]):
    _type_: ClassVar[type[C.c_ushort]] = C.c_ushort

    def __class_getitem__(cls, params: Any) -> Any:
        return _shared_class_getitem(cls, params)


# float arrays
class CDoubleArray(CArray[float, C.c_double]):
    _type_: ClassVar[type[C.c_double]] = C.c_double

    def __class_getitem__(cls, params: Any) -> Any:
        return _shared_class_getitem(cls, params)


class CFloatArray(CArray[float, C.c_float]):
    _type_: ClassVar[type[C.c_float]] = C.c_float

    def __class_getitem__(cls, params: Any) -> Any:
        return _shared_class_getitem(cls, params)


class CLongDoubleArray(CArray[float, C.c_longdouble]):
    _type_: ClassVar[type[C.c_longdouble]] = C.c_longdouble

    def __class_getitem__(cls, params: Any) -> Any:
        return _shared_class_getitem(cls, params)

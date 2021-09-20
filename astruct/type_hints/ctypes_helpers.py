# This file is generated by _gen_ctypes_info.py

from typing import Annotated, Any, Protocol
from typing import _GenericAlias  # type: ignore
import ctypes as C
from .carray import _CIntArray, _CFloatArray
from .metadata import CField

# pyright: reportPrivateUsage=none

__all__ = ['CByte', 'CInt', 'CInt16', 'CInt32', 'CInt64', 'CInt8', 'CLong', 'CLongLong', 'CShort',
           'CSizeT', 'CSSizeT', 'CUByte', 'CUInt', 'CUInt16', 'CUInt32', 'CUInt64', 'CUInt8',
           'CULong', 'CULongLong', 'CUShort', 'CDouble', 'CFloat', 'CLongDouble', 'CByteArray',
           'CIntArray', 'CInt16Array', 'CInt32Array', 'CInt64Array', 'CInt8Array', 'CLongArray',
           'CLongLongArray', 'CShortArray', 'CSizeTArray', 'CSSizeTArray', 'CUByteArray',
           'CUIntArray', 'CUInt16Array', 'CUInt32Array', 'CUInt64Array', 'CUInt8Array',
           'CULongArray', 'CULongLongArray', 'CUShortArray', 'CDoubleArray', 'CFloatArray',
           'CLongDoubleArray']

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


# int arrays
class CByteArray(_CIntArray[C.c_byte], Protocol):
    def __class_getitem__(cls, params: Any) -> _GenericAlias:  # type: ignore
        if not isinstance(params, int):
            raise TypeError('Expected a single integer as a type parameter')

        return _GenericAlias(cls, params)  # type: ignore


class CIntArray(_CIntArray[C.c_int], Protocol):
    def __class_getitem__(cls, params: Any) -> _GenericAlias:  # type: ignore
        if not isinstance(params, int):
            raise TypeError('Expected a single integer as a type parameter')

        return _GenericAlias(cls, params)  # type: ignore


class CInt16Array(_CIntArray[C.c_int16], Protocol):
    def __class_getitem__(cls, params: Any) -> _GenericAlias:  # type: ignore
        if not isinstance(params, int):
            raise TypeError('Expected a single integer as a type parameter')

        return _GenericAlias(cls, params)  # type: ignore


class CInt32Array(_CIntArray[C.c_int32], Protocol):
    def __class_getitem__(cls, params: Any) -> _GenericAlias:  # type: ignore
        if not isinstance(params, int):
            raise TypeError('Expected a single integer as a type parameter')

        return _GenericAlias(cls, params)  # type: ignore


class CInt64Array(_CIntArray[C.c_int64], Protocol):
    def __class_getitem__(cls, params: Any) -> _GenericAlias:  # type: ignore
        if not isinstance(params, int):
            raise TypeError('Expected a single integer as a type parameter')

        return _GenericAlias(cls, params)  # type: ignore


class CInt8Array(_CIntArray[C.c_int8], Protocol):
    def __class_getitem__(cls, params: Any) -> _GenericAlias:  # type: ignore
        if not isinstance(params, int):
            raise TypeError('Expected a single integer as a type parameter')

        return _GenericAlias(cls, params)  # type: ignore


class CLongArray(_CIntArray[C.c_long], Protocol):
    def __class_getitem__(cls, params: Any) -> _GenericAlias:  # type: ignore
        if not isinstance(params, int):
            raise TypeError('Expected a single integer as a type parameter')

        return _GenericAlias(cls, params)  # type: ignore


class CLongLongArray(_CIntArray[C.c_longlong], Protocol):
    def __class_getitem__(cls, params: Any) -> _GenericAlias:  # type: ignore
        if not isinstance(params, int):
            raise TypeError('Expected a single integer as a type parameter')

        return _GenericAlias(cls, params)  # type: ignore


class CShortArray(_CIntArray[C.c_short], Protocol):
    def __class_getitem__(cls, params: Any) -> _GenericAlias:  # type: ignore
        if not isinstance(params, int):
            raise TypeError('Expected a single integer as a type parameter')

        return _GenericAlias(cls, params)  # type: ignore


class CSizeTArray(_CIntArray[C.c_size_t], Protocol):
    def __class_getitem__(cls, params: Any) -> _GenericAlias:  # type: ignore
        if not isinstance(params, int):
            raise TypeError('Expected a single integer as a type parameter')

        return _GenericAlias(cls, params)  # type: ignore


class CSSizeTArray(_CIntArray[C.c_ssize_t], Protocol):
    def __class_getitem__(cls, params: Any) -> _GenericAlias:  # type: ignore
        if not isinstance(params, int):
            raise TypeError('Expected a single integer as a type parameter')

        return _GenericAlias(cls, params)  # type: ignore


class CUByteArray(_CIntArray[C.c_ubyte], Protocol):
    def __class_getitem__(cls, params: Any) -> _GenericAlias:  # type: ignore
        if not isinstance(params, int):
            raise TypeError('Expected a single integer as a type parameter')

        return _GenericAlias(cls, params)  # type: ignore


class CUIntArray(_CIntArray[C.c_uint], Protocol):
    def __class_getitem__(cls, params: Any) -> _GenericAlias:  # type: ignore
        if not isinstance(params, int):
            raise TypeError('Expected a single integer as a type parameter')

        return _GenericAlias(cls, params)  # type: ignore


class CUInt16Array(_CIntArray[C.c_uint16], Protocol):
    def __class_getitem__(cls, params: Any) -> _GenericAlias:  # type: ignore
        if not isinstance(params, int):
            raise TypeError('Expected a single integer as a type parameter')

        return _GenericAlias(cls, params)  # type: ignore


class CUInt32Array(_CIntArray[C.c_uint32], Protocol):
    def __class_getitem__(cls, params: Any) -> _GenericAlias:  # type: ignore
        if not isinstance(params, int):
            raise TypeError('Expected a single integer as a type parameter')

        return _GenericAlias(cls, params)  # type: ignore


class CUInt64Array(_CIntArray[C.c_uint64], Protocol):
    def __class_getitem__(cls, params: Any) -> _GenericAlias:  # type: ignore
        if not isinstance(params, int):
            raise TypeError('Expected a single integer as a type parameter')

        return _GenericAlias(cls, params)  # type: ignore


class CUInt8Array(_CIntArray[C.c_uint8], Protocol):
    def __class_getitem__(cls, params: Any) -> _GenericAlias:  # type: ignore
        if not isinstance(params, int):
            raise TypeError('Expected a single integer as a type parameter')

        return _GenericAlias(cls, params)  # type: ignore


class CULongArray(_CIntArray[C.c_ulong], Protocol):
    def __class_getitem__(cls, params: Any) -> _GenericAlias:  # type: ignore
        if not isinstance(params, int):
            raise TypeError('Expected a single integer as a type parameter')

        return _GenericAlias(cls, params)  # type: ignore


class CULongLongArray(_CIntArray[C.c_ulonglong], Protocol):
    def __class_getitem__(cls, params: Any) -> _GenericAlias:  # type: ignore
        if not isinstance(params, int):
            raise TypeError('Expected a single integer as a type parameter')

        return _GenericAlias(cls, params)  # type: ignore


class CUShortArray(_CIntArray[C.c_ushort], Protocol):
    def __class_getitem__(cls, params: Any) -> _GenericAlias:  # type: ignore
        if not isinstance(params, int):
            raise TypeError('Expected a single integer as a type parameter')

        return _GenericAlias(cls, params)  # type: ignore


# float arrays
class CDoubleArray(_CFloatArray[C.c_double], Protocol):
    def __class_getitem__(cls, params: Any) -> _GenericAlias:  # type: ignore
        if not isinstance(params, int):
            raise TypeError('Expected a single integer as a type parameter')

        return _GenericAlias(cls, params)  # type: ignore


class CFloatArray(_CFloatArray[C.c_float], Protocol):
    def __class_getitem__(cls, params: Any) -> _GenericAlias:  # type: ignore
        if not isinstance(params, int):
            raise TypeError('Expected a single integer as a type parameter')

        return _GenericAlias(cls, params)  # type: ignore


class CLongDoubleArray(_CFloatArray[C.c_longdouble], Protocol):
    def __class_getitem__(cls, params: Any) -> _GenericAlias:  # type: ignore
        if not isinstance(params, int):
            raise TypeError('Expected a single integer as a type parameter')

        return _GenericAlias(cls, params)  # type: ignore
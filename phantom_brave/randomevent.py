import ctypes as C

from astruct import typed_struct
from astruct.type_hints import *
from utils import CountedTable


@typed_struct
class RandomEvent(C.Structure):
    _pack_ = 1

    id: CUInt16
    title: CStr[31]
    subtitle: CStr[31]
    _unk: CUInt8Array[52]


class RandomEventTable(CountedTable[RandomEvent]):
    STANDARD_FILENAME = 'revent.dat'

    def __init__(self, buffer: WriteableBuffer, offset: int = 0) -> None:
        super().__init__(RandomEvent, buffer, offset)

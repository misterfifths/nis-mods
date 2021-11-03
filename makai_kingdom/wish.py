import ctypes as C
from typing import Final

from astruct import typed_struct
from astruct.type_hints import *
from utils import CountedTable


@typed_struct
class Wish(C.Structure):
    _pack_ = 1

    mana_cost: CUInt32
    level_req: CUInt16
    id: CUInt16
    _zero: CUInt8
    name: CStr[63]
    description: CStr[64]  # TODO: why the length difference?


class WishTable(CountedTable[Wish]):
    STANDARD_FILENAME: Final = 'WISH.DAT'

    def __init__(self, buffer: WriteableBuffer, offset: int = 0) -> None:
        super().__init__(Wish, buffer, offset)

import ctypes as C
from typing import Final

from platform_config import PSP

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

    _NAME_LEN: Final[int] = 63 if PSP else 81
    name: CStr[_NAME_LEN]

    _DESCRIPTION_LEN: Final[int] = 64 if PSP else 106
    description: CStr[_DESCRIPTION_LEN]


class WishTable(CountedTable[Wish]):
    STANDARD_FILENAME: Final = 'WISH.DAT'

    def __init__(self, buffer: WriteableBuffer, offset: int = 0) -> None:
        super().__init__(Wish, buffer, offset)

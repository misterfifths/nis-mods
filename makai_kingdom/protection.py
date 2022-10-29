import ctypes as C

from platform_config import PSP

from astruct import typed_struct
from astruct.type_hints import *
from utils import CountedTable


@typed_struct
class Protection(C.Structure):
    _pack_ = 1

    id: CUInt8

    _NAME_LEN: int = 22 if PSP else 21
    name: CStr[_NAME_LEN]

    if PSP:
        # This field is just missing in the PC/Switch re-release
        description: CStr[57]


class ProtectionTable(CountedTable[Protection]):
    STANDARD_FILENAME = 'PROTECTION.DAT'

    def __init__(self, buffer: WriteableBuffer, offset: int = 0) -> None:
        super().__init__(Protection, buffer, offset)

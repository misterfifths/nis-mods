import ctypes as C

from astruct import typed_struct
from astruct.type_hints import *
from utils import CountedTable


@typed_struct
class SpecialSkill(C.Structure):
    _pack_ = 1

    id: CUInt16
    _unk1: CUInt8Array[8]
    name: CStr[17]
    description: CStr[57]  # not sure on length
    _unk2: CUInt8Array[82]


class SpecialSkillsTable(CountedTable[SpecialSkill]):
    STANDARD_FILENAME = 'magic.dat'

    def __init__(self, buffer: WriteableBuffer, offset: int = 0) -> None:
        super().__init__(SpecialSkill, buffer, offset, double_counted=False)

    def special_for_name(self, name: str) -> SpecialSkill:
        for skill in self:
            if skill.name == name:
                return skill

        raise KeyError(f'No special skill named {name!r}')

    def special_for_id(self, id: int) -> SpecialSkill:
        for skill in self:
            if skill.id == id:
                return skill

        raise KeyError(f'No special skill with id {id:#x}')

import ctypes as C

from astruct import typed_struct
from astruct.type_hints import *
from utils import CountedTable


@typed_struct
class Skill(C.Structure):
    _pack_ = 1

    id: CUInt16
    name: CStr[18]
    description: CStr[58]
    _unk: CUInt8Array[14]


class SkillTable(CountedTable[Skill]):
    STANDARD_FILENAME = 'Skill.dat'

    def __init__(self, buffer: WriteableBuffer, offset: int = 0) -> None:
        super().__init__(Skill, buffer, offset, double_counted=False)

    def skill_for_name(self, name: str) -> Skill:
        for skill in self:
            if skill.name == name:
                return skill

        raise KeyError(f'No skill named {name!r}')

    def skill_for_id(self, id: int) -> Skill:
        for skill in self:
            if skill.id == id:
                return skill

        raise KeyError(f'No skill with id {id:#x}')

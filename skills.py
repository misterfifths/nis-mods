from typing import Final
import ctypes as C
from astruct import typed_struct
from astruct.type_hints import *
from countedtable import CountedTable


@typed_struct
class Skill(C.Structure):
    _pack_ = 1

    mana_cost: CUInt32
    id: CUInt16
    _unk1: CUInt8Array[2]
    sp_cost: CUInt16
    _zero: CUInt8Array[2]  # maybe sp_cost is 32 bits?
    name: CStr[22]
    description: CStr[70]
    _unk2: CUInt8Array[8]
    sp_type: CUInt8
    shape: CUInt8  # 0=sphere, 1=cylinder, 2=wedge
    _unk3: CUInt8Array[3]
    distance: CUInt8
    range: CUInt8
    vertical: CUInt8Array[2]
    _unk4: CUInt8Array[7]


class SkillTable(CountedTable[Skill]):
    STANDARD_FILENAME: Final = 'magic.dat'

    def __init__(self, buffer: WriteableBuffer, offset: int = 0) -> None:
        super().__init__(Skill, buffer, offset)

    def skill_for_name(self, name: str) -> Skill:
        for skill in self:
            if skill.name == name:
                return skill

        raise KeyError(f'No skill named "{name}"')

    def skill_for_id(self, id: int) -> Skill:
        for skill in self:
            if skill.id == id:
                return skill

        raise KeyError(f'No skill with id {id:#x}')

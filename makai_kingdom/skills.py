import ctypes as C
from typing import Annotated, Final

from astruct import typed_struct
from astruct.type_hints import *
from utils import CountedTable


@typed_struct
class Skill(C.Structure):
    _pack_ = 1

    _unk1: CUInt8Array[4]
    id: CUInt16
    _unk2: CUInt8Array[2]
    sp_cost: CUInt32
    name: CStr[22]

    # The description field uses \x87 as the escape sequence for inline icons,
    # as used for special effects and elements. That's not valid shift-jis, so
    # we're using this error handler to round-trip them more nicely.
    description: Annotated[CStr[56], Encoding(errors='backslashreplace')]

    _unk3: CUInt8Array[22]


class SkillTable(CountedTable[Skill]):
    STANDARD_FILENAME: Final = 'MAGIC.DAT'

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

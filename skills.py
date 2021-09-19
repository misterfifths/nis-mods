import ctypes as C
from typing import Annotated, ClassVar, Optional, Sequence
from astruct import typed_struct, CStrField, CField
from countedtable import CountedTable
from utils import WriteableBuffer


@typed_struct
class Skill(C.Structure):
    _pack_: ClassVar[int] = 1

    mana_cost: Annotated[int, CField(C.c_uint32)]
    id: Annotated[int, CField(C.c_uint16)]
    _unk1: Annotated[Sequence[int], CField(C.c_uint8 * 2)]
    sp_cost: Annotated[int, CField(C.c_uint16)]
    _zero: Annotated[Sequence[int], CField(C.c_uint8 * 2)]  # maybe sp_cost is 32 bits?
    name: Annotated[str, CStrField(22)]
    description: Annotated[str, CStrField(70)]
    _unk2: Annotated[Sequence[int], CField(C.c_uint8 * 8)]
    sp_type: Annotated[int, CField(C.c_uint8)]
    shape: Annotated[int, CField(C.c_uint8)]  # 0=sphere, 1=cylinder, 2=wedge
    _unk3: Annotated[Sequence[int], CField(C.c_uint8 * 3)]
    distance: Annotated[int, CField(C.c_uint8)]
    range: Annotated[int, CField(C.c_uint8)]
    vertical: Annotated[Sequence[int], CField(C.c_uint8 * 2)]
    _unk4: Annotated[Sequence[int], CField(C.c_uint8 * 7)]


class SkillTable(CountedTable[Skill]):
    STANDARD_FILENAME: ClassVar[str] = 'magic.dat'

    def __init__(self, buffer: WriteableBuffer, offset: int = 0) -> None:
        super().__init__(Skill, buffer, offset)

    def skill_for_name(self, name: str) -> Optional[Skill]:
        for skill in self._entries:
            if skill.name == name:
                return skill

        return None

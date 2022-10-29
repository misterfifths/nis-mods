import ctypes as C
from typing import Annotated, Final, Iterable

from astruct import typed_struct
from astruct.type_hints import *
from utils import CountedTable


@typed_struct
class Skill(C.Structure):
    _pack_ = 1

    # Meaning varies depending on skill. For e.g. Purify Range +X, this is the
    # range boost. For most with a hard-coded effect (e.g. Super Dodge), this
    # is just 1.
    strength: CUInt16

    # 1 if this skill is randomly activated at the beginning of an attack. 0
    # if it's a permanent effect that's always on (e.g. movement bonuses)
    is_randomly_activated: CUInt16

    id: CUInt8

    # Characters can only have one skill in a given category - learning a more
    # powerful one overwrites the weaker. For example, all the Purify Power +X
    # skills have category ID 0x90e. Purify Power +6 overrides Purify Power +5.
    # Skills with only one level (e.g. Chakra) are alone in their category.
    category_id: CUInt16

    _zero: CUInt8

    # Minimum attribute levels required to learn the skill. In the order given
    # by ItemStatIndex.
    attr_requirements: CUInt8Array[8]

    name: Annotated[CStr[35], Encoding('wide_shift_jis')]
    description: Annotated[CStr[75], Encoding('wide_shift_jis')]


assert C.sizeof(Skill) == 126


class SkillTable(CountedTable[Skill]):
    STANDARD_FILENAME: Final = 'skill.dat'

    def __init__(self, buffer: WriteableBuffer, offset: int = 0) -> None:
        super().__init__(Skill, buffer, offset)

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

    def skills_for_category(self, category_id: int) -> Iterable[Skill]:
        for skill in self:
            if skill.category_id == category_id:
                yield skill

import ctypes as C
import enum
from typing import Annotated, Final

from astruct import typed_struct
from astruct.type_hints import *
from utils import CountedTable


@enum.unique
class SkillKind(enum.IntEnum):
    ACTIVE = 0x00
    BUILDING = 0x02  # Building invites are secretly skills
    PASSIVE = 0x0a


@enum.unique
class SkillEffectType(enum.IntEnum):
    # Unsure of the unit on this. Corresponds to the "Power" column of skills
    # in the strategy guide.
    POWER_BOOST = 0x01

    UNKNOWN_BASE_PANEL = 0x02  # On untranslated skills about the base panel?

    # The amount for these is a percent buff/debuff.
    ATK_UP = 0x0b  # e.g. Braveheart
    DEF_UP = 0x0c  # e.g. Shield
    INT_UP = 0x0d  # e.g. Magic Boost
    RES_UP = 0x0e  # e.g. Magic Wall
    TEC_UP = 0x0f  # Only on Laboratory invite and unavailable Chakra skill

    # The amount for these is a percent chance.
    POISON = 0x15
    SLEEP = 0x16
    PARALYZE = 0x17
    AMNESIA = 0x18
    DAZED = 0x19
    GAMBLE = 0x1a

    # These are boosts upon killing an effected enemy.
    # Amount is the percent boost.
    HL_UP = 0x1f  # Only on Shop invite and unavailable Mega Bonus skill
    EXP_UP = 0x20  # Only on Academy invite and unavailable Mega Bonus skill
    MANA_UP = 0x21  # e.g. the Box skills, Library invite

    # These have fixed amounts.
    CURE_STATUS = 0x65  # Espoir (amount is always 20)
    ABSORB_HP = 0x66  # e.g. Syringe skills (amount is always 100)

    # This is only on one unavailable skill called Carol. Its description says
    # "Recovers multiple targets from incapacity." Amount is always 20.
    UNKNOWN_REVIVE = 0x67


@enum.unique
class SkillElement(enum.IntEnum):
    NONE = 0
    FIRE = 1
    WIND = 2
    ICE = 3


@enum.unique
class SkillProficiency(enum.IntEnum):
    NONE = 0
    ANTI_VEHICLE = 1  # 50% damage boost against vehicles
    ANTI_BUILDING = 2  # 50% damage boost against buildings


@enum.unique
class SkillStat(enum.IntEnum):
    PASSIVE = 0x00  # All passive skills have this value

    # Both normal RES-based healing skills and TEC-based wrench skills that
    # repair vehicles have this value.
    HEALING_RES_OR_TEC = 0x04

    NONE = 0x05  # Skills like Espoir that do not depend on any stat
    BASIC_ATK_OR_INT = 0x07  # Power Strike (ATK) and Energy Blast (INT)
    SP = 0x0b  # Balloon skills
    ATK = 0x0c
    INT = 0x0e
    RES = 0x0f  # Healing skills have value 0x04 though
    TEC = 0x10


@typed_struct
class Skill(C.Structure):
    _pack_ = 1

    # For weapon skills, this is the mastery level needed in that weapon in
    # order to unlock the skill. It's 0 for weapon skills for which you don't
    # need any mastery (e.g. Sniper Edge on daggers). It's 0 for all non-weapon
    # skills (they're either available from the start on non-weapon items, like
    # Armor Press, or assigned a learn level on the class that learns them).
    mastery_level: CUInt16
    _zero1: CUInt8Array[2]
    id: CUInt16
    _unk1: CUInt8Array[2]
    sp_cost: CUInt32
    name: CStr[22]

    # The description field uses \x87 as the escape sequence for inline icons,
    # as used for special effects and elements. That's not valid shift-jis, so
    # we're using this error handler to round-trip them more nicely.
    description: Annotated[CStr[56], Encoding(errors='backslashreplace')]

    _zero2: CUInt8

    # Strength of special effects applied by this skill. Effect types are in
    # the corresponding index in the effect_types list. See the SkillEffectType
    # enumeration for details on each type and the meaning of the amount.
    effect_amounts: CInt8Array[5]

    kind: CUInt8  # One of the values from the SkillKind enumeration
    _unk2: CUInt8Array[2]
    damage_proficiency: CUInt8  # See SkillProficiency enumeration
    element: CUInt8  # One of the values from the SkillElement enumeration
    stat: CUInt8  # See SkillStat enumeration
    _unk3: CUInt8Array[4]

    # IDs of special effects applied by this skill. Strengths of the effects
    # are in the corresponding index in the effect_amounts list. See the
    # SkillEffectType for possible values. The list is terminated by a zero.
    effect_types: CUInt8Array[5]

    _unk4: CUInt8


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

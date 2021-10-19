import ctypes as C
import enum
from typing import Final

from astruct import typed_struct
from astruct.type_hints import *
from utils import CountedTable


@enum.unique
class ClassType(enum.IntEnum):
    BUILDING_VEHICLE_OR_UNIQUE_MALE = 1
    UNIQUE_FEMALE = 2
    GENERIC_MALE = 11
    GENERIC_FEMALE = 12


@enum.unique
class StatIndex(enum.IntEnum):
    """The indexes into various Class arrays that correspond to core stats."""
    HP = 0
    SP = 1
    ATK = 2
    DEF = 3
    INT = 4
    RES = 5
    TEC = 6


@typed_struct
class Class(C.Structure):
    _pack_ = 1

    class_name: CStr[22]  # For uniques, this is their name (e.g. "Asagi")

    # For uniques, confusingly this is their class name (e.g. "Gunner" for
    # Asagi). For generics, this is the name of the rank within their class
    # (e.g. all Prinnies have class_name "Prinny", but they have names like
    # "Prinny Leader" or "Prinny God" depending on rank.)
    name: CStr[21]

    # Note that Asagi's description is misaligned in the translation by default
    description: CStr[58]
    type: CUInt8  # One of the ClassType enumeration values
    _unk1: CUInt8Array[2]

    # For generic characters, the rank within their class (starting at 0). With
    # only a few exceptions, this is otherwise zero.
    rank: CUInt8

    vehicle_flag: CUInt8  # 2 for all vehicles, otherwise zero
    jump: CUInt8
    building_flag: CUInt8  # 2 for all buildings, otherwise 1
    aptitudes: CUInt8Array[7]  # In the order of the StatIndex enumeration
    _unk2: CUInt8Array[11]

    # Characters always have character_slots == 1, and total_slots is the
    # number of equipment/item slots they have. For buildings and vehicles,
    # the two numbers are always equal. I imagine it has something to do with
    # whether a slot is for an item or can also be a character, hence the names
    # I chose.
    character_slots: CUInt8
    total_slots: CUInt8

    _unk3: CUInt8Array[2]
    id: CUInt16

    # If the appearance of this class is based off another, the other class's
    # id is given here. For example, all higher ranks of a class point back to
    # the id of the lowest rank in that class. Uniques with the appearance of
    # another class will point to that here as well (e.g., Raiden points to
    # the lowest rank Thunder God). Uniques with a unique appearance will point
    # to their own id. I don't understand how buildings work; they seem to have
    # their own values for this field that aren't ids of a class at all.
    visual_id: CUInt16

    _unk4: CUInt8Array[4]
    throw: CUInt16
    growth_rates: CUInt16Array[7]  # In the order of the StatIndex enumeration

    _zero: CUInt8Array[2]
    _five: CUInt16  # constant 5?
    move: CUInt16
    _unk5: CUInt16Array[2]
    hl_bonus: CUInt16
    exp_bonus: CUInt16
    _unk6: CUInt16Array[2]
    mana_bonus: CUInt16

    # The IDs of the passive skills for this class. Unlike in Phantom Brave,
    # classes learn passives as they level, but the passives themselves do not
    # have experience levels. The level at which the class learns a passive is
    # at the corresponding index in the passive_skill_learn_levels list. The
    # list is terminated with a zero.
    passive_skill_ids: CUInt16Array[24]

    # The level at which the class learns passive skills. The order is the same
    # as the IDs in passive_skill_ids.
    passive_skill_levels: CUInt16Array[24]

    # The IDs of the active skills learned by this class. The level at which
    # the class learns the skills are in the corresponding index in the
    # active_skill_learn_levels list. The list is terminated with a zero.
    active_skill_ids: CUInt16Array[16]

    # The level at which a character learns active skills. The order is the
    # same as the IDs in active_skill_ids.
    active_skill_learn_levels: CUInt16Array[16]

    mana_cost: CUInt32

    @property
    def is_building(self) -> bool:
        return self.building_flag == 2

    @property
    def is_vehicle(self) -> bool:
        return self.vehicle_flag == 2

    @property
    def is_character(self) -> bool:
        return not self.is_building and not self.is_vehicle

    @property
    def is_generic_character(self) -> bool:
        return self.is_character and \
            self.type in (ClassType.GENERIC_FEMALE, ClassType.GENERIC_MALE)

    @property
    def is_male(self) -> bool:
        return self.is_character and \
            self.type in (ClassType.GENERIC_MALE, ClassType.BUILDING_VEHICLE_OR_UNIQUE_MALE)

    @property
    def is_female(self) -> bool:
        return self.is_character and not self.is_male


class ClassTable(CountedTable[Class]):
    STANDARD_FILENAME: Final = 'CHAR.DAT'

    def __init__(self, buffer: WriteableBuffer, offset: int = 0) -> None:
        super().__init__(Class, buffer, offset)

    def class_for_class_name(self, class_name: str) -> Class:
        for cls in self:
            if cls.class_name == class_name:
                return cls

        raise KeyError(f'No class with the class_name "{class_name}"')

    def class_for_name(self, name: str) -> Class:
        for cls in self:
            if cls.name == name:
                return cls

        raise KeyError(f'No class with the name "{name}"')

    def class_for_id(self, id: int) -> Class:
        for cls in self:
            if cls.id == id:
                return cls

        raise KeyError(f'No class with the id {id:#x}')

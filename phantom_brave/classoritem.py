import ctypes as C
import enum
from typing import Final

from astruct import typed_struct
from astruct.type_hints import *
from utils import CountedTable

from .fusioncompat import fusion_compat_name_for_id


@enum.unique
class ClassStatIndex(enum.IntEnum):
    """The indexes into various ClassOrItem arrays that correspond to core
    stats."""
    HP = 0
    # The second field is unused and always zero. I'd wager this is a holdover
    # from Disgaea, which had a single SP stat.
    ATK = 2
    DEF = 3
    INT = 4
    RES = 5
    SPD = 6


@enum.unique
class SPTypeIndex(enum.IntEnum):
    """The indexes into ClassOrItem.sp_aptitude for particular types of SP."""
    PHYSICAL = 0
    ENERGY = 1
    ELEMENTAL = 2
    NATURE = 3
    SPACETIME = 4
    STAT = 5
    HEAL = 6


@typed_struct
class ClassOrItem(C.Structure):
    _pack_ = 1

    # The name of an instance of this class or item. For generic classes and
    # items, it's the same as class_name.
    name: CStr[22]  # TODO: length discrepancy between this and class_name?
    class_name: CStr[21]
    description: CStr[73]
    _unk1: CUInt8Array[6]
    jump: CUInt8
    _unk2: CUInt8  # either 1 or 2, but no idea why

    # Aptitudes with the types of SP. Arranged in the order defined in the
    # SPTypeIndex enumeration. The range (via the strategy guide) seems to be
    # this:
    #  1 -  3: F
    #  4 -  6: E
    #  7 - 10: D
    # 11 - 14: C
    # 15 - 17: B
    # 18 - 20: A
    # 21+    : S
    sp_aptitudes: CUInt8Array[7]
    _zero1: CUInt8

    # Rank doesn't seem to be very meaningful for classes. For generics, the
    # recruitment cost from Marona is 5 * (rank + 1). E.g., DungeonMonk's rank
    # is 100, resulting in a base recruitment cost of 505 BOR.
    rank: CUInt8
    guard: CUInt16
    _unk3: CUInt8  # some sort of flag for bosses?
    id: CUInt16

    # If the visuals of this class/item are based on another, this field is set
    # to the ID of the other class/item. Otherwise it's equal to id.
    visual_id: CUInt16
    _unk4: CUInt8Array[4]
    throw: CUInt16

    # Growth rates for the core stats, arranged in the order defined in the
    # ClassStatIndex enumeration.
    growth_rates: CUInt16Array[7]
    _zero2: CUInt8Array[2]

    # The effects on various stats of being confined into this item. Compute
    # the actual values by subtracting 100 from these integers. Array elements
    # are in the order defined in the ClassStatIndex enumeration.
    confine_rates: CUInt16Array[7]
    _zero3: CUInt8Array[2]

    # The percentage of stats that are transferred to the wielder when an
    # object with this class is equipped. These values are never negative; you
    # do not need to subtract 100 like you do for confine_rates. Array elements
    # are in the order defined in the ClassStatIndex enumeration.
    equip_rates: CUInt16Array[7]
    _zero4: CUInt8Array[2]
    _five: CUInt16  # constant 5. weird.
    move: CUInt16
    _zero5: CUInt8Array[2]
    steal: CUInt16
    bor_bonus: CUInt16
    exp_bonus: CUInt16
    _unk5: CUInt8Array[2]

    # The fusion compatibility category ID for this class/item. See the
    # fusioncompat module for tools to handle this.
    compat_category_id: CUInt16
    remove: CUInt16

    # The IDs of the passive skills for this class. Unlike active skills, these
    # are available from level 1 for the character. The experience level for
    # each passive skill is at the corresponding index in the
    # passive_skill_levels list. The list is terminated with a zero.
    passive_skill_ids: CUInt16Array[8]

    # The experience level known passive skills. The order is the same as the
    # IDs in passive_skill_ids.
    passive_skill_levels: CUInt16Array[8]

    # The IDs of the active skills learned by this class. Unlike passive
    # skills, these are unlocked when a character reaches a certain level.
    # Those levels are in the corresponding index in the
    # active_skill_learn_levels list. The list is terminated with a zero.
    active_skill_ids: CUInt16Array[16]

    # The level at which a character learns active skills. The order is the
    # same as the IDs in active_skill_ids. For items, a learn level of 0 means
    # the skill is purchaseable from a Blacksmith, but not normally unlocked.
    active_skill_learn_levels: CUInt16Array[16]

    # Zero for everyone but Ash and Marona
    _unk6: CUInt8Array[2]
    _zero6: CUInt8Array[2]

    @property
    def is_item(self) -> bool:
        return self.id >= 0xf00  # no magic here, just from inspecting the existing entries

    @property
    def is_class(self) -> bool:
        return not self.is_item

    @property
    def compat_category_name(self) -> str:
        try:
            return fusion_compat_name_for_id(self.compat_category)
        except KeyError:
            return f'(unknown: {self.compat_category})'

    def _get_free_skill_index(self, passive: bool) -> int:
        ids = self.passive_skill_levels if passive else self.active_skill_ids
        for i, id in enumerate(ids):
            if id == 0:
                return i

        if passive:
            raise IndexError('No room to add a passive skill')
        raise IndexError('No room to add an active skill')

    def add_passive_skill_id(self, skill_id: int, level: int) -> None:
        free_idx = self._get_free_skill_index(passive=True)
        self.passive_skill_ids[free_idx] = skill_id
        self.passive_skill_levels[free_idx] = level

    def add_active_skill_id(self, skill_id: int, learn_level: int) -> None:
        free_idx = self._get_free_skill_index(passive=False)
        self.active_skill_ids[free_idx] = skill_id
        self.active_skill_learn_levels[free_idx] = learn_level

    def index_of_passive_skill_id(self, skill_id: int) -> int:
        for i, sid in enumerate(self.passive_skill_ids):
            if sid == skill_id:
                return i

        raise ValueError(f'Skill id {skill_id} is not in passive skills')

    def index_of_active_skill_id(self, skill_id: int) -> int:
        for i, sid in enumerate(self.active_skill_ids):
            if sid == skill_id:
                return i

        raise ValueError(f'Skill id {skill_id} is not in active skills')

    def has_skill_id(self, skill_id: int) -> bool:
        return skill_id in self.passive_skill_ids or skill_id in self.active_skill_ids


class ClassOrItemTable(CountedTable[ClassOrItem]):
    STANDARD_FILENAME: Final = 'char.dat'

    def __init__(self, buffer: WriteableBuffer, offset: int = 0) -> None:
        super().__init__(ClassOrItem, buffer, offset)

    def entry_for_class_name(self, class_name: str) -> ClassOrItem:
        for coi in self:
            if coi.class_name == class_name:
                return coi

        raise KeyError(f'No class or item with the class_name {class_name!r}')

    def entry_for_id(self, id: int) -> ClassOrItem:
        for coi in self:
            if coi.id == id:
                return coi

        raise KeyError(f'No class or item with id {id:#x}')

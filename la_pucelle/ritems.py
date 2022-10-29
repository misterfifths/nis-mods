import ctypes as C
import enum
from typing import Annotated, Final, Sequence

from astruct import typed_struct
from astruct.type_hints import *
from utils import CountedTable

"""
Random items from the Dark World are assembled with three components, which are
all represented by variations on the same structure in ritem.dat. The
components are:

1. A prefix. This is the source of the base cost of the item, its description,
   any special effects, and its "stat basis" (more on that in a minute).
2. An item base. This determines the actual type of the assembled item (weapon,
   armor, or accessory), its icon, and the distribution of its stats.
3. Some added "flavor." This adds additional text to the assembled item's
   description and adjusts its cost. (TODO: I'm not certain whether the flavor
   also affects stats.)

The name of an assembled item is its prefix's name + the base's name.

The cost of an assembled item is:
    prefix.cost * (base.stat_basis_or_cost_multiplier +
                   flavor.stat_basis_or_cost_multiplier) / 100

The stats of an assembled item are determined by multiplying its prefix's
stat basis by the per-stat multipliers on its base. The stat multipliers are
percentages and may be negative. For example the ATK of a given item is:
    prefix.stat_basis_or_cost_multiplier *
        base.stat_multipliers[ItemStatIndex.ATK] / 100
"""


@enum.unique
class RItemKind(enum.IntEnum):
    PREFIX = 11
    FLAVOR = 31

    # Item bases
    WEAPON = 1
    ARMOR = 2
    ACCESSORY = 3


@typed_struct
class RItem(C.Structure):
    _pack_ = 1

    cost: CUInt32  # See above; zero for everything but prefixes

    # Flavors have an empty string for their name
    name: Annotated[CStr[21], Encoding('wide_shift_jis')]

    # All RItem kinds have a description, but the ones on item bases are not
    # used in the description of assembled items.
    description: Annotated[CStr[69], Encoding('wide_shift_jis')]

    # See note above. These are zero for prefixes and flavors.
    # These are in the same order as ItemStatIndex.
    stat_multipliers: CInt16Array[8]

    kind: CUInt16  # one of RItemKind

    rank: CUInt16  # only prefixes are ranked; other kinds have value 0
    rarity: CUInt16  # maybe? lower = less likely? majority have value 100

    icon: CUInt16  # only on item bases

    # This is only set on item bases. Seems to be some sort of categorization.
    # All weapons have value 1, all accessories 6, but armor is split:
    # shields 2, body armor 3, headgear 4, boots 5. Maybe for generating enemy
    # gear? Wouldn't want more than one item from each category?
    _unk: CUInt16

    # See note above. For prefixes, this is the stat basis. For item bases and
    # flavor, this is a multiplier to determine the cost of an assembled item.
    stat_basis_or_cost_multiplier: CUInt16

    special_effect_id: CUInt16  # See above; zero for everything but prefixes

    _zero: CUInt8Array[4]

    @property
    def is_prefix(self) -> bool:
        return self.kind == RItemKind.PREFIX

    @property
    def is_item_base(self) -> bool:
        return self.kind in (RItemKind.WEAPON, RItemKind.ARMOR, RItemKind.ACCESSORY)

    @property
    def is_flavor(self) -> bool:
        return self.kind == RItemKind.FLAVOR


class RItemTable(CountedTable[RItem]):
    STANDARD_FILENAME: Final = 'ritem.dat'

    prefixes: Sequence[RItem]
    item_bases: Sequence[RItem]
    flavors: Sequence[RItem]

    def __init__(self, buffer: WriteableBuffer, offset: int = 0) -> None:
        super().__init__(RItem, buffer, offset)

        self.prefixes = []
        self.item_bases = []
        self.flavors = []

        for ritem in self:
            if ritem.is_prefix:
                self.prefixes.append(ritem)
            elif ritem.is_item_base:
                self.item_bases.append(ritem)
            elif ritem.is_flavor:
                self.flavors.append(ritem)
            else:
                raise ValueError(f'Unknown RItem kind {ritem.kind:#x}')

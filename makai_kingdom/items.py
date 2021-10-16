import ctypes as C
import enum
from typing import Final

from astruct import typed_struct
from astruct.type_hints import *
from utils import CountedTable


@enum.unique
class ElementalResType(enum.IntFlag):
    """Possible values for the entries in the elemental_res_types list of
    Items."""
    FIRE = 1 << 0
    WIND = 1 << 1
    ICE = 1 << 2


@enum.unique
class StatusResType(enum.IntFlag):
    """Possible values for the entries in the status_res_types list of
    Items."""
    POISON = 1 << 0
    SLEEP = 1 << 1
    PARALYZE = 1 << 2
    AMNESIA = 1 << 3
    DAZED = 1 << 4
    GAMBLE = 1 << 5


@typed_struct
class Item(C.Structure):
    _pack_ = 1

    name: CStr[21]
    description: CStr[57]
    rank: CUInt8
    _unk1: CUInt8Array[3]

    # assuming this is signed like move, but there are no negative examples
    jump: CInt16

    _unk2: CUInt8Array[3]

    # All "environmental objects" (rocks, trees, flowers, etc.) have the same
    # category ID (0). Aside from that, each type of weapon/armor/vehicle
    # equipment/food/etc. has its own category id.
    category_id: CUInt8

    _unk3: CUInt8Array[4]
    id: CUInt16
    _unk4: CUInt8Array[6]
    move: CInt16
    equip_stats: CInt16Array[7]
    _unk5: CUInt8Array[4]
    confine_percents: CUInt16Array[7]

    # An item can differently effect up to 2 elemental resistances and 2
    # resistances to status effects. The _types arrays contain codes for the
    # types of resistances effected, some combination of flags from the
    # ElementalResType and StatusResType enumerations. The _amounts arrays
    # contain (at corresponding indexes) the percent buff/debuff to the
    # resistance. The _types arrays are terminated by a zero.
    # For example, if elemental_res_types is [3 (FIRE | WIND), 4 (ICE)],
    # and elemental_res_amounts is [10, -20], the item will imbue a 10% boost
    # to the fire and wind resistances, and a -20% debuff to wind resistance.
    elemental_res_types: CUInt16Array[2]
    elemental_res_amounts: CInt16Array[2]

    status_res_types: CUInt16Array[2]
    status_res_amounts: CInt16Array[2]

    # Active skills on weapons are learned at particular levels of your mastery
    # with that weapon type. The mastery level needed for each skill is in the
    # corresponding index of active_skill_mastery_levels. The list is
    # terminated by a zero.
    active_skill_ids: CUInt16Array[12]
    active_skill_mastery_levels: CUInt16Array[12]

    _zero: CUInt8Array[2]

    hl_cost: CUInt32
    mt_cost: CUInt32


class ItemTable(CountedTable[Item]):
    STANDARD_FILENAME: Final = 'MITEM.DAT'

    def __init__(self, buffer: WriteableBuffer, offset: int = 0) -> None:
        super().__init__(Item, buffer, offset)

    def item_for_name(self, name: str) -> Item:
        for item in self:
            if item.name == name:
                return item

        raise KeyError(f'No item with the name "{name}"')

    def item_for_id(self, id: int) -> Item:
        for item in self:
            if item.id == id:
                return item

        raise KeyError(f'No item with the id {id:#x}')
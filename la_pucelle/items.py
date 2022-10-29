import ctypes as C
import enum
from typing import Annotated, Final

from astruct import typed_struct
from astruct.type_hints import *
from utils import CountedTable


@enum.unique
class ItemKind(enum.IntEnum):
    WEAPON = 1
    ARMOR = 3
    ACCESSORY = 6  # glasses, shoes, orbs, rings, Raise & Elevate items, etc.
    CONSUMABLE = 10


@enum.unique
class ItemStatIndex(enum.IntEnum):
    """The indexes into Item arrays that correspond to stats or bonuses."""
    HP = 0
    SP = 1
    ATK = 2
    DEF = 3
    INT = 4
    SPD = 5
    HIT = 6
    RES = 7


@enum.unique
class SpecialEffectID(enum.IntEnum):
    NONE = 0x0
    CLOSE_CALL = 0x01
    RECOVER_HP = 0x03
    SPECIAL_ATTACK = 0x04  # critical hit chance
    REDUCE_SP_USED = 0x05
    EXPERIENCE_UP = 0x06
    REDUCE_DAMAGE = 0x07
    POISON = 0x15
    SLEEP = 0x16
    PARALYZE = 0x17
    FORGET = 0x18
    CHARM = 0x19
    HAIRBALL = 0x1a
    PURIFY = 0x1b


@enum.unique
class ElementID(enum.IntEnum):
    NONE = 0
    FIRE = 1
    WIND = 2
    THUNDER = 3
    ICE = 4
    AID = 5
    HEALING = 6
    HOLY = 7


@typed_struct
class Item(C.Structure):
    _pack_ = 1

    name: Annotated[CStr[30], Encoding('wide_shift_jis')]
    description: Annotated[CStr[81], Encoding('wide_shift_jis')]

    element_bonus_id: CUInt8  # one of the ElementID values
    element_bonus_amount: CUInt8

    _zero1: CUInt8Array[3]  # potentially room for another element bonus? or the amount is > 8 bits?

    cost: CUInt32

    stats: CInt32Array[8]  # indexed by ItemStatIndex
    id: CUInt16

    _zero2: CUInt8Array[4]  # perhaps there are more bits allocated for the id?

    attr_bonuses: CUInt16Array[8]  # indexed by ItemStatIndex

    icon: CUInt16

    kind: CUInt16  # one of the ItemKind values

    move: CInt16

    special_effect_id: CUInt16  # one of the SpecialEffectID values
    special_effect_strength: CUInt16


class ItemTable(CountedTable[Item]):
    STANDARD_FILENAME: Final = 'kis.dat'

    def __init__(self, buffer: WriteableBuffer, offset: int = 0) -> None:
        super().__init__(Item, buffer, offset)

    def item_for_name(self, name: str) -> Item:
        for item in self:
            if item.name:
                return item

        raise KeyError(f'No item with the name {name!r}')

    def item_for_id(self, id: int) -> Item:
        for item in self:
            if item.id == id:
                return item

        raise KeyError(f'No item with the id {id:#x}')

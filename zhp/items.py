import ctypes as C
import enum
from typing import Final, Iterable, Optional

from astruct import typed_struct
from astruct.type_hints import *
from utils import CountedTable, ro_cached_property

from .item_categories import ItemCategory, ItemKind


@enum.unique
class ItemStatIndex(enum.IntEnum):
    HP = 0
    # The second field is unused and always zero. I'd wager this is a holdover
    # from Disgaea, which had a single SP stat.
    SAT = 2
    SDF = 3
    LAT = 4
    SPD = 5
    HIT = 6
    LDF = 7


@enum.unique
class ItemResistanceIndex(enum.IntEnum):
    FIRE = 0
    WIND = 1
    WATER = 2


class ItemCondLossSources(enum.IntFlag):
    NONE = 0
    ATTACK = 1
    DAMAGE_TAKEN = 2


@typed_struct
class Item(C.Structure):
    _pack_ = 1

    name: CStr[17]
    description: CStr[58]

    _unk1: CUInt8
    rank: CUInt8  # Star count

    _unk2: CUInt8Array[2]
    jump: CUInt8
    _unk3: CUInt8Array[8]

    stats: CInt16Array[8]  # In the order of ItemStatIndex

    # This id is not unique! Versions of the same item with different ranks
    # share an id. The combination of (id, rank) *is* unique.
    id: CUInt16

    # The category property looks this id up and returns a more useful
    # ItemCategory object.
    category_id: CUInt8

    _zero1: CUInt8
    skill_id: CUInt16
    _unk5: CUInt8Array[24]

    resistances: CInt8Array[3]  # In the order of ItemResistanceIndex

    _unk6: CUInt8Array[3]

    # A portion of COND can be lost when attacking, taking damage, or both.
    # The sources that cause loss are some combination of ItemCondLossSources
    # in cond_lost_sources. The amount lost per attack/damage is in the
    # cond_loss field.
    cond_loss_sources: CUInt8
    cond_loss: CUInt8

    _unk7: CUInt8Array[54]

    @ro_cached_property
    def category(self) -> ItemCategory:
        return ItemCategory.category_for_id(self.category_id)

    @property
    def kind(self) -> ItemKind:
        return self.category.kind


class ItemTable(CountedTable[Item]):
    STANDARD_FILENAME: Final = 'ItemParam.dat'

    def __init__(self, buffer: WriteableBuffer, offset: int = 0) -> None:
        super().__init__(Item, buffer, offset, double_counted=False)

    def items_for_name(self, name: str) -> Iterable[Item]:
        for item in self:
            if item.name == name:
                yield item

    def item_for_name(self, name: str, rank: Optional[int] = None) -> Item:
        items = list(self.items_for_name(name))

        if len(items) == 0:
            raise KeyError(f'No item with name {name!r}')

        if rank is not None:
            for item in items:
                if item.rank == rank:
                    return item

            raise KeyError(f'No item with name {name!r} has a rank of {rank}')

        if len(items) == 1:
            return items[0]

        raise KeyError(f'Multiple items exist with name {name!r}; specify a rank')

    def items_for_id(self, id: int) -> Iterable[Item]:
        for item in self:
            if item.id == id:
                yield item

    def item_for_id(self, id: int, rank: Optional[int] = None) -> Item:
        items = list(self.items_for_id(id))

        if len(items) == 0:
            raise KeyError(f'No item with id {id:#x}')

        if rank is not None:
            for item in items:
                if item.rank == rank:
                    return item

            raise KeyError(f'No item with id {id:#x} has a rank of {rank}')

        if len(items) == 1:
            return items[0]

        raise KeyError(f'Multiple items exist with id {id:#x}; specify a rank')

from typing import Final, Iterable
import ctypes as C
import enum
from astruct import typed_struct
from astruct.type_hints import *
from countedtable import CountedTable
from utils import WriteableBuffer


@enum.unique
class MemberKind(enum.IntEnum):
    CLASS_OR_ITEM = 0
    CATEGORY = 1


@typed_struct
class DungeonCategory(C.Structure):
    MAX_MEMBER_COUNT: Final = 20

    _pack_ = 1

    id: CUInt8
    _zero: CUInt8

    # These are the IDs of the members of this category. They are either
    # literal item/enemy class IDs, or encoded references to other categories
    # (making this a category of categories, like Cutlery or Item).
    # The length might actually be fewer than 20; the maximum seen is UbeRare,
    # which has 19. Only member_count many values in this list are considered,
    # and all remaining slots should be zero.
    # You likely want to use the members property instead of this, as it
    # decodes the integers for you.
    member_codes: CUInt16Array[MAX_MEMBER_COUNT]
    _zero2: CUInt16  # always zero. Perhaps part of member_codes?
    name: CStr[8]  # this is probably length 7
    _zero3: CUInt8Array[3]

    # The minimum level at which a Dungeon Monk can roll this category.
    monk_level_req: CUInt8

    # Likelihood of this category rolling. Translate to a percentage by
    # calculating 100% - this value; a category with rarity 100 never rolls.
    rarity: CUInt8

    # The number of valid entries in member_codes.
    member_count: CUInt8

    @classmethod
    def decode_member_code(cls, code: int) -> tuple[MemberKind, int]:
        is_category = (code & 0xff00) == 0xea00
        if is_category:
            return (MemberKind.CATEGORY, code - 0xea60)

        return (MemberKind.CLASS_OR_ITEM, code)

    @classmethod
    def member_code_for_category(cls, category_id: int) -> int:
        return category_id + 0xea60

    @property
    def members(self) -> Iterable[tuple[MemberKind, int]]:
        for i in range(self.member_count):
            yield self.decode_member_code(self.member_codes[i])

    @property
    def is_item_category(self) -> bool:
        return self.id >= 0x65

    @property
    def is_weapon_category(self) -> bool:
        return self.id >= 0x84

    @property
    def is_enemy_category(self) -> bool:
        return not self.is_item_category

    def remove_all_members(self) -> None:
        for i in range(len(self.member_codes)):
            self.member_codes[i] = 0

        self.member_count = 0

    def add_member(self, kind: MemberKind, member_id: int) -> None:
        if self.member_count >= self.MAX_MEMBER_COUNT:
            raise IndexError(f'No space for new member {member_id} in category {self.name}')

        new_code = member_id
        if kind == MemberKind.CATEGORY:
            new_code = self.member_code_for_category(member_id)

        self.member_codes[self.member_count] = new_code
        self.member_count += 1


class DungeonCategoryTable(CountedTable[DungeonCategory]):
    STANDARD_FILENAME: Final = 'runit.dat'

    def __init__(self, buffer: WriteableBuffer, offset: int = 0) -> None:
        super().__init__(DungeonCategory, buffer, offset)

    def category_for_name(self, name: str) -> DungeonCategory:
        for cat in self:
            if cat.name == name:
                return cat

        raise KeyError(f'No category named "{name}"')

    def category_for_id(self, id: int) -> DungeonCategory:
        for cat in self:
            if cat.id == id:
                return cat

        raise KeyError(f'No category with id {id:#x}')

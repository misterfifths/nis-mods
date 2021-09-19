import ctypes as C
from typing import Annotated, ClassVar, Iterable, Sequence
from astruct import typed_struct, CStrField, CField
from countedtable import CountedTable
from utils import FixedLengthMutableSequence, WriteableBuffer
import enum


@enum.unique
class MemberKind(enum.IntEnum):
    CLASS_OR_ITEM = 0
    CATEGORY = 1


@typed_struct
class DungeonCategory(C.Structure):
    _pack_: ClassVar[int] = 1

    MAX_MEMBER_COUNT: ClassVar[int] = 20

    id: Annotated[int, CField(C.c_uint8)]
    _zero: Annotated[int, CField(C.c_uint8)]

    # These are the IDs of the members of this category. They are either
    # literal item/enemy class IDs, or encoded references to other categories
    # (making this a category of categories, like Cutlery or Item).
    # The length might actually be fewer than 20; the maximum seen is UbeRare,
    # which has 19. Only member_count many values in this list are considered,
    # and all remaining slots should be zero.
    # You likely want to use the members property instead of this, as it
    # decodes the integers for you.
    member_codes: Annotated[FixedLengthMutableSequence[int], CField(C.c_uint16 * MAX_MEMBER_COUNT)]
    _zero2: Annotated[int, CField(C.c_uint16)]  # always zero. Perhaps part of member_codes?
    name: Annotated[str, CStrField(8)]  # this is probably length 7
    _zero3: Annotated[Sequence[int], CField(C.c_uint8 * 3)]

    # The minimum level at which a Dungeon Monk can roll this category.
    monk_level_req: Annotated[int, CField(C.c_uint8)]

    # Likelihood of this category rolling. Translate to a percentage by
    # calculating 100% - this value; a category with rarity 100 never rolls.
    rarity: Annotated[int, CField(C.c_uint8)]

    # The number of valid entries in member_codes.
    member_count: Annotated[int, CField(C.c_uint8)]

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
    STANDARD_FILENAME: ClassVar[str] = 'runit.dat'

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

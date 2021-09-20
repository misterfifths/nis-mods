from typing import ClassVar
import ctypes as C
import enum
from astruct import typed_struct
from astruct.type_hints import *
from countedtable import CountedTable
from utils import WriteableBuffer


@enum.unique
class Rarity(enum.IntEnum):
    # Can be found on random items/enemies, items in the store, or characters
    # from Marona.
    NORMAL = 0

    # Can only be found on items in random dungeons after the given floor.
    AFTER_FLOOR_10 = 1
    AFTER_FLOOR_30 = 2
    AFTER_FLOOR_60 = 3

    # Any other value for the rarity field means it's not obtainable via normal
    # means. Either it's enemy-only, or in the case of Combo, Blasphm, and
    # Unliked, requires some special action to acquire.
    SPECIAL_AND_BOSES = 0x51  # Blasphm, Unliked, and some boss titles
    SNAKISH = 0x61  # ... don't know why this gets its own category
    ENEMIES_ONLY_2 = 0x62  # SuprOL, EvilSwd, and one untranslated one
    ENEMIES_ONLY_AND_COMBO = 0x63  # The majority of enemy-only titles (+Combo)


@enum.unique
class TitleStatIndex(enum.IntEnum):
    HP = 0
    ATK = 1
    DEF = 2
    INT = 3
    RES = 4
    SPD = 5


@typed_struct
class Title(C.Structure):
    _pack_: ClassVar[int] = 1

    id: CUInt16
    name: CStr[9]  # max length w/o nulls seems to be 7

    # exp_bonus and bor_bonus should be multiplied by 5% to find the actual
    # percentage. So the max is 0x7f * 5% = 635%.
    exp_bonus: CUInt8
    bor_bonus: CUInt8

    # The changes to the palette when this title is applied to a character.
    # (Unsure of the exact format.)
    color_change: CUInt8

    # Obtainable titles are ranks 0-7, but there are some unobtainable rank 8s.
    rank: CUInt8

    rarity: CUInt8

    # These are encoded strangely; see the elemental_resistances getter for
    # details.
    _elemental_resistances: CUInt8

    guard: CUInt8
    steal: CUInt8
    move: CUInt8

    # Bonuses to each stat from this title, in the order defined by the
    # TitleStatIndex enumeration. Compute the percentage by subtracting these
    # values from 100; e.g. 100 = no change, 0 = -100%, 255 = +155%.
    stat_bonuses: CUInt8Array[6]

    # Bonuses to aptitude for SP types from this title. Arranged in the order
    # defined in the SPTypeIndex enumeration. These values added to the base
    # skill SP aptitude of the character/item with the title.
    sp_bonuses: CInt8Array[7]

    _zero: CUInt8Array[3]

    # Skills conferred by this title. List is terminated by a zero.
    skill_ids: CUInt16Array[4]

    @property
    def elemental_resistances(self) -> tuple[int, int, int]:
        """Returns a tuple of the title's bonus to fire, wind, and ice
        resistance, in that order."""

        # The resistances on a title always sum to zero. Values 1-10 favor
        # fire resistance, 11-20 favor wind, and 21-30 favor ice. The favored
        # element gets up to +100%, and the other two elements each get
        # -1/2 of the bonus given to the favored, so it all balances out.

        res = self._elemental_resistances
        fire_res = wind_res = ice_res = 0

        if res <= 10:
            fire_res = res * 10
            wind_res = ice_res = res * -5
        elif res <= 20:
            res -= 10
            wind_res = res * 10
            fire_res = ice_res = res * -5
        elif res <= 30:
            res -= 20
            ice_res = res * 10
            fire_res = wind_res = res * -5

        return (fire_res, wind_res, ice_res)


class TitleTable(CountedTable[Title]):
    STANDARD_FILENAME: ClassVar[str] = 'ItemPowUp.dat'

    def __init__(self, buffer: WriteableBuffer, offset: int = 0) -> None:
        super().__init__(Title, buffer, offset)

    def title_for_name(self, name: str) -> Title:
        for title in self:
            if title.name == name:
                return title

        raise KeyError(f'No title named "{name}"')

    def category_for_id(self, id: int) -> Title:
        for title in self:
            if title.id == id:
                return title

        raise KeyError(f'No title with id {id:#x}')

import ctypes as C
from typing import Final

from astruct import typed_struct
from astruct.type_hints import *
from utils import CountedTable

# Couldn't find an in-game source of these names; these are taken from the
# strategy guide.
FUSION_COMPAT_CATEGORY_NAMES = {
    0: '(special)',

    1: 'Warrior',
    2: 'Magic',
    3: 'Support',
    4: 'Nature',
    5: 'Normal',
    6: 'BeastMan',
    7: 'Beast',
    8: 'Slime',
    9: 'Fairy',
    10: 'Spirit',
    11: 'Dragon',

    21: 'Sword',
    22: 'Axe',
    23: 'Spear',
    24: 'Staff',
    25: 'Book',

    31: 'Tree',
    32: 'Plant',
    33: 'Rock',
    34: 'Dead Tree',
    35: 'Food',
    36: 'Mailbox',  # only the special Mailbox entity

    41: 'Vase',  # also a few unrelated Another Marona items
    42: 'Skull',
    43: 'Tool',
    44: 'Bomb',  # also Steel Alloy from Another Marona
    45: 'Interior'
}


def fusion_compat_name_for_id(id: int) -> str:
    return FUSION_COMPAT_CATEGORY_NAMES[id]


def fusion_compat_id_for_name(name: str) -> int:
    for id, cat_name in FUSION_COMPAT_CATEGORY_NAMES.items():
        if name == cat_name:
            return id

    raise KeyError(f'Unknown fusion compatibility category name "{name}"')


"""
aishou.dat is layed out like a grid. It's easiest to explain with an example.
Say the rows in aishou.dat looked like this (the actual file has many more
rows and columns; this is simplified):

0f 01 02 03 0a 1b
01 10 64 64 64 64
02 10 10 10 10 10
03 20 30 20 50 60
0a 1e 1e 20 10 1e
1b 1e 1e 1e 1e 10

The first row is a header that define the meanings of each column. The first
entry in the first row is the constant 0x0f and can be ignored. After that are
a list of compatibility IDs that appear in that particular column.

From the second row onward, the first element is the compatibility ID whose
stats follow in the rest of the row.

Rows correspond to beneficiaries (i.e., the recipient of the fusion) and
columns correspond to material (i.e., the donor item/character that will be
lost in the fusion).

So to find the compatibility when, say, fusing a material with compatibility
ID 03 to a beneficiary of ID 0a, we scan down to find the row whose first
element is 0a, then move to the column corresponding to 03 (which is the 4th),
and we have the compatibility 0x20.

The final step is to compute 100 - that number. So we find in our previous
example, 0a (beneficiary) + 03 (material) has a compatibility of 100 - 32 = 68.

Note that, like in this example, the compatibility relationship is not always
symmetrical; which is the material and which is the beneficiary matters.

In the struct below, the first entry in each row is assigned to the field
label. The actual columns in the row are in the entries array, followed by some
padding zero bytes.
"""


@typed_struct
class FusionCompatibilityRow(C.Structure):
    _pack_ = 1

    label: CUInt8
    entries: CUInt8Array[26]
    _zero: CUInt8Array[37]


class FusionCompatibilityTable(CountedTable[FusionCompatibilityRow]):
    STANDARD_FILENAME: Final = 'aishou.dat'

    _column_order: list[int]

    def __init__(self, buffer: WriteableBuffer, offset: int = 0) -> None:
        super().__init__(FusionCompatibilityRow, buffer, offset)

        # list() here is working around the fact that ctypes.Arrays don't have
        # index().
        self._column_order = list(self[0].entries)

    def _column_idx_for_id(self, id: int) -> int:
        try:
            return self._column_order.index(id)
        except ValueError as e:
            raise KeyError(f'Unknown fusion compatibility category ID {id}') from e

    def _row_for_id(self, id: int) -> FusionCompatibilityRow:
        for row in self[1:]:  # skip the header
            if row.label == id:
                return row

        raise KeyError(f'Unknown fusion compatibility category ID {id}')

    def compatibility_for_ids(self, id_beneficiary: int, id_material: int) -> int:
        column_idx = self._column_idx_for_id(id_material)
        return self._row_for_id(id_beneficiary).entries[column_idx]

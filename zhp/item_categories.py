import enum
from enum import auto


@enum.unique
class ItemKind(enum.IntEnum):
    EQUIPMENT = auto()  # Non-weapon equipment
    WEAPON = auto()
    SHADOWGRAM_ITEM = auto()
    HEALING_CONSUMABLE = auto()  # Energy and HP healing items
    DUNGEON_CONSUMABLE = auto()  # Status-inflicting and movement items
    MONEY = auto()  # As an item on the ground in dungeons
    DENGEKI_CARD = auto()
    RARE_METAL = auto()


class ItemCategory(enum.Enum):
    # Equipment
    HEAD_EQUIP = (0x00, 'Head Equipment', ItemKind.EQUIPMENT)
    EXPANSION_EQUIP = (0x01, 'Expansion Equipment', ItemKind.EQUIPMENT)
    LEFT_ARM_EQUIP = (0x02, 'L Arm Equipment', ItemKind.EQUIPMENT)
    RIGHT_ARM_EQUIP = (0x03, 'R Arm Equipment', ItemKind.EQUIPMENT)
    LEG_EQUIP = (0x04, 'Leg Equipment', ItemKind.EQUIPMENT)
    DRAGON_CLAW = (0x41, 'Dragon Claw', ItemKind.EQUIPMENT)  # not sure why this is so special

    # Weapons
    GUN = (0x06, 'Gun', ItemKind.WEAPON)
    MELEE_WEAPON = (0x10, 'Melee Weapon', ItemKind.WEAPON)  # Swords, Axes, Spears
    STAFF = (0x11, 'Staff', ItemKind.WEAPON)

    # Shadowgram items
    # Most Shadowgram items are type 0x14, with some exceptions.
    BOOSTER_PLUG = (0x14, 'Booster Plug', ItemKind.SHADOWGRAM_ITEM)
    CHANGER = (0x15, 'Changer', ItemKind.SHADOWGRAM_ITEM)
    CONTAINER = (0x31, 'Container', ItemKind.SHADOWGRAM_ITEM)  # S/M/L Container chips
    LIFE_SUPPORT = (0x32, 'Life Support', ItemKind.SHADOWGRAM_ITEM)
    CAPSULE = (0x30, 'Capsule', ItemKind.SHADOWGRAM_ITEM)  # S/M/L Capsule chips

    # Consumables
    # Healing items
    HEALING_ITEM = (0x34, 'HP Healing Item', ItemKind.HEALING_CONSUMABLE)  # HP/status healing items
    FOOD = (0x16, 'EN Healing Item', ItemKind.HEALING_CONSUMABLE)  # E.g., meats, lunches

    # Dungeon use items
    BARRIER_STONE = (0x61, 'Barrier Stone', ItemKind.DUNGEON_CONSUMABLE)
    POISON_BOTTLE = (0x35, 'Poison Bottle', ItemKind.DUNGEON_CONSUMABLE)
    SOFT_PILLOW = (0x36, 'Soft Pillow', ItemKind.DUNGEON_CONSUMABLE)
    PARALYZE_BOX = (0x54, 'Paralyze Box', ItemKind.DUNGEON_CONSUMABLE)
    FLASHBANG = (0x60, 'Flashbang', ItemKind.DUNGEON_CONSUMABLE)
    HAMMER = (0x07, 'Hammer', ItemKind.DUNGEON_CONSUMABLE)
    CONFUSION_TUB = (0x55, 'Confusion Tub', ItemKind.DUNGEON_CONSUMABLE)
    DEAD_WEIGHT = (0x57, 'Dead Weight', ItemKind.DUNGEON_CONSUMABLE)
    JUMP_DEVICE = (0x37, 'Jump Device', ItemKind.DUNGEON_CONSUMABLE)

    # Miscellaneous
    MONEY = (0x1f, 'Money', ItemKind.MONEY)  # As an item on the ground in dungeons
    DENGEKI_CARD = (0x62, 'Dengeki Card', ItemKind.DENGEKI_CARD)

    RARE_METAL_SAT = (0x08, 'Rare Metal (Red - SAT)', ItemKind.RARE_METAL)
    RARE_METAL_SDF = (0x0a, 'Rare Metal (Orange - SDF)', ItemKind.RARE_METAL)
    RARE_METAL_LAT = (0x0b, 'Rare Metal (Yellow - LAT)', ItemKind.RARE_METAL)
    RARE_METAL_LDF = (0x0c, 'Rare Metal (Blue - LDF)', ItemKind.RARE_METAL)
    RARE_METAL_HIT = (0x0d, 'Rare Metal (Green - HIT)', ItemKind.RARE_METAL)
    RARE_METAL_SPD = (0x0e, 'Rare Metal (Teal - SPD)', ItemKind.RARE_METAL)
    RARE_METAL_GRAY = (0x0f, 'Rare Metal (Gray)', ItemKind.RARE_METAL)  # No stat boost

    def __init__(self, id: int, friendly_name: str, kind: ItemKind) -> None:
        self.id = id
        self.friendly_name = friendly_name
        self.kind = kind

    @classmethod
    def category_for_id(cls, id: int) -> 'ItemCategory':
        for cat in cls:
            if cat.id == id:
                return cat

        raise KeyError(f'No item category with id {id:#x}')

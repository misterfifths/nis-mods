import enum
from enum import auto
from typing import Optional


@enum.unique
class ItemKind(enum.IntEnum):
    ENVIRONMENTAL_OBJECT = auto()  # Trees, rocks, flowers, etc.
    WEAPON = auto()
    ARMOR = auto()
    ACCESSORY = auto()
    VEHICLE_EQUIPMENT = auto()
    CONSUMABLE = auto()  # Food and "travel items" like Divers
    SPECIAL = auto()  # Unobtainable items


class ItemCategory(enum.Enum):
    OBJECT = (0x00, 'Environmental Object', ItemKind.ENVIRONMENTAL_OBJECT)

    DAGGER = (0x01, 'Dagger', ItemKind.WEAPON)
    SWORD = (0x02, 'Sword', ItemKind.WEAPON)
    KATANA = (0x03, 'Katana', ItemKind.WEAPON)
    BEAM_SABER = (0x04, 'Beam Sword', ItemKind.WEAPON)
    AXE = (0x05, 'Axe', ItemKind.WEAPON)
    FRYING_PAN = (0x06, 'Frying Pan', ItemKind.WEAPON)
    MORNINGSTAR = (0x07, 'Morningstar', ItemKind.WEAPON)
    NUNCHAKU = (0x08, 'Nunchaku', ItemKind.WEAPON)
    MALLET = (0x09, 'Hammer', ItemKind.WEAPON)
    SPEAR = (0x0a, 'Spear', ItemKind.WEAPON)
    RAPIER = (0x0b, 'Rapier', ItemKind.WEAPON)
    SYRINGE = (0x0c, 'Syringe', ItemKind.WEAPON)
    FISHING_POLE = (0x0d, 'Fishing Pole', ItemKind.WEAPON)
    RIFLE = (0x0e, 'Rifle', ItemKind.WEAPON)
    FLAME_THROWER = (0x0f, 'Flame Thrower', ItemKind.WEAPON)
    GATLING = (0x10, 'Gatling', ItemKind.WEAPON)
    BAZOOKA = (0x11, 'Bazooka', ItemKind.WEAPON)
    CANNON = (0x12, 'Cannon', ItemKind.WEAPON)
    WRENCH = (0x13, 'Wrench', ItemKind.WEAPON)
    SHOVEL = (0x14, 'Shovel', ItemKind.WEAPON)
    REMOTE = (0x15, 'Remote', ItemKind.WEAPON)
    BOMB = (0x16, 'Bomb', ItemKind.WEAPON)
    DRILL = (0x17, 'Drill', ItemKind.WEAPON)
    BOOK = (0x18, 'Book', ItemKind.WEAPON)
    STAFF = (0x19, 'Staff', ItemKind.WEAPON)
    FAN = (0x1a, 'Fan', ItemKind.WEAPON)
    MAGNET = (0x1b, 'Magnet', ItemKind.WEAPON)
    DRUM = (0x1c, 'Drum', ItemKind.WEAPON)
    PIE = (0x1d, 'Pie', ItemKind.WEAPON)
    BALLOON = (0x1e, 'Balloon', ItemKind.WEAPON)
    BOX = (0x1f, 'Box', ItemKind.WEAPON)
    UFO = (0x20, 'UFO', ItemKind.WEAPON)

    ROBE = (0x33, 'Robe', ItemKind.ARMOR)
    LT_ARMOR = (0x34, 'Lt. Armor', ItemKind.ARMOR)
    HV_ARMOR = (0x35, 'Hv. Armor', ItemKind.ARMOR)
    SHIELD = (0x36, 'Shield', ItemKind.ARMOR)
    CAPE = (0x37, 'Cape', ItemKind.ARMOR)
    HELMET = (0x38, 'Helmet', ItemKind.ARMOR)
    HAT = (0x39, 'Hat', ItemKind.ARMOR)

    BELT = (0x3a, 'Belt', ItemKind.ACCESSORY)
    SHOES = (0x3b, 'Shoes', ItemKind.ACCESSORY)
    ORB = (0x3c, 'Orb', ItemKind.ACCESSORY)
    RING = (0x3d, 'Ring', ItemKind.ACCESSORY)
    GLASSES = (0x3e, 'Glasses', ItemKind.ACCESSORY)
    MUSCLE = (0x3f, 'Muscle', ItemKind.ACCESSORY)
    CHARM = (0x40, 'Charm', ItemKind.ACCESSORY)
    TREASURE = (0x41, 'Treasure', ItemKind.ACCESSORY)

    VEHICLE_ARMOR = (0x65, 'Vehicle Armor', ItemKind.VEHICLE_EQUIPMENT)
    AMMO = (0x66, 'Ammo', ItemKind.VEHICLE_EQUIPMENT)
    TANK = (0x67, 'Tank', ItemKind.VEHICLE_EQUIPMENT)
    ENGINE = (0x68, 'Engine', ItemKind.VEHICLE_EQUIPMENT)
    BARRIER = (0x69, 'Barrier', ItemKind.VEHICLE_EQUIPMENT)
    BOOSTER = (0x6a, 'Booster', ItemKind.VEHICLE_EQUIPMENT)
    OS = (0x6b, 'OS', ItemKind.VEHICLE_EQUIPMENT)
    WHEEL = (0x6c, 'Wheel', ItemKind.VEHICLE_EQUIPMENT)

    FOOD1 = (0x97, 'Food', ItemKind.CONSUMABLE)
    FOOD2 = (0x98, 'Food', ItemKind.CONSUMABLE)
    FOOD3 = (0x99, 'Food', ItemKind.CONSUMABLE)
    TRAVEL_ITEM = (0x9b, 'Travel item', ItemKind.CONSUMABLE)

    SPECIAL = (0xa0, 'Special', ItemKind.SPECIAL)

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

    @property
    def mastery_skill_name(self) -> Optional[str]:
        """For weapons, returns the name of the associated mastery skill. For
        other types of items, returns None.

        The skill object can be looked up in the SkillTable by this name.
        """
        if self.kind == ItemKind.WEAPON:
            return self.friendly_name  # engineered it so that this is the same

        return None

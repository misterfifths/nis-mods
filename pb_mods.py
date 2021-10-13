#!/usr/bin/env python3

import os
import sys
import mmap
from pathlib import Path
from phantom_brave import *


def _add_item_to_category(cat_name: str, item_class_name: str, start_dat: StartDatArchive) -> None:
    cat = start_dat.cattab.category_for_name(cat_name)
    item = start_dat.classtab.entry_for_class_name(item_class_name)

    print(f'Adding {item.name} to category {cat.name}')
    cat.add_member(CategoryMemberKind.CLASS_OR_ITEM, item.id)


def add_another_marona_items_to_pools(start_dat: StartDatArchive) -> None:
    additions = (
        ('Food', 'Watermelon'),
        ('Food', 'Fishcake'),
        ('Grass', 'Weed?'),
        ('Plant', 'Weed?'),
        ('Plant', 'Watermelon'),
        ('Fish', 'Fishcake'),
        ('Fish', 'Shell'),
        ('Tool', 'Bonfire'),
        ('Tool', 'Steel Alloy'),
        ('Tool', 'Bell'),
        ('Tool', 'Fan'),
        ('Box', 'Bell')
    )

    print('\n>> Adding Another Marona items to dungeon item pools...')

    for cat_name, item_class_name in additions:
        _add_item_to_category(cat_name, item_class_name, start_dat)


def normalize_dungeon_category_rarities(start_dat: StartDatArchive) -> None:
    print('\n>> Normalizing roll rates of dungeon item pools...')
    for cat in start_dat.cattab:
        if cat.rarity != 100:  # keep the unrollable ones that way
            cat.rarity = 0


def create_rarity_category(start_dat: StartDatArchive) -> None:
    # The category we're taking over
    donor_cat_name = 'Garden'

    # Where to move that category's items, so they're still available
    items_to_move = (
        ('Box', 'Vase'),
        ('Plant', 'Seed'),
        ('Box', 'Pot'),
        ('Tool', 'Water Can')
    )

    new_items = (
        'Egg',
        'Hourglass',
        'Candle',
        'Changebook'
    )

    print('\n>> Creating Rarity dungeon item pool...')
    print(f'(moving items from donor category "{donor_cat_name}")')

    cat = start_dat.cattab.category_for_name(donor_cat_name)

    # Move its old items
    for cat_name, item_class_name in items_to_move:
        _add_item_to_category(cat_name, item_class_name, start_dat)

    print(f'(configuring new category)')

    cat.name = 'Rarity'
    cat.monk_level_req = 75
    cat.rarity = 50
    cat.remove_all_members()
    for item_class_name in new_items:
        _add_item_to_category(cat.name, item_class_name, start_dat)


def maximize_fusion_compatibility(start_dat: StartDatArchive) -> None:
    MAX_COMPAT = 10  # --> 90% / SSS

    print('\n>> Maximizing fusion compatibilities...')

    for row in start_dat.compattab[1:]:  # skipping the header row
        for i in range(len(row.entries)):
            row.entries[i] = MAX_COMPAT


# This is actually on the conservative side, all things considered.
# def adjust_skill_mana_costs(start_dat: StartDatArchive) -> None:
#     for skill in start_dat.skilltab:
#         if skill.mana_cost >= 100000:
#             skill.mana_cost = 10000
#         else:
#             skill.mana_cost //= 2

def adjust_skill_costs_big_time(start_dat: StartDatArchive) -> None:
    print('\n>> Adjusting skill mana and SP costs...')

    for skill in start_dat.skilltab:
        new_mana_cost = skill.mana_cost // 5
        new_mana_cost = min(250, new_mana_cost)

        new_sp_cost = skill.sp_cost // 3
        if skill.sp_cost > 0:
            new_sp_cost = max(1, new_sp_cost)

        skill.mana_cost = new_mana_cost
        skill.sp_cost = new_sp_cost


def adjust_passive_skill_levels(start_dat: StartDatArchive) -> None:
    adjustments = (
        ('Mystic', 'Healing Birth', 40),
        ('Knight', 'Healing Steps', 40),
        ('DungeonMonk', 'EXP. Riser', 40),
        ('Merchant', 'Made of Money', 40),
        ('Blacksmith', 'Mana Monger', 40)
    )

    print('\n>> Adjusting passive skill levels...')

    for class_name, skill_name, new_level in adjustments:
        cls = start_dat.classtab.entry_for_class_name(class_name)
        skill = start_dat.skilltab.skill_for_name(skill_name)

        skill_idx = cls.index_of_passive_skill_id(skill.id)
        old_level = cls.passive_skill_levels[skill_idx]

        print(f'bumping {skill_name} on {class_name} from level {old_level} to {new_level}')
        cls.passive_skill_levels[skill_idx] = new_level


def adjust_failure_title_bonuses(start_dat: StartDatArchive) -> None:
    print('\n>> Adjusting Failure title EXP and BOR bonuses...')

    failure_title = start_dat.titletab.title_for_name('Failure')

    # The int value of these fields is multiplied by 5%, so this is a 20% boost
    failure_title.exp_bonus = failure_title.bor_bonus = 4


def increase_bottlemail_steal(start_dat: StartDatArchive) -> None:
    print('\n>> Increasing Bottlemail\'s STEAL stat...')

    bmail = start_dat.classtab.entry_for_class_name('Bottlemail')
    bmail.steal = 100


def make_thief_title(start_dat: StartDatArchive) -> None:
    print('\n>>> Making Thief title...')

    donor = start_dat.titletab.title_for_name('DieNow')

    print(f'(overwriting donor title "{donor.name}")')
    donor.name = 'Thief'

    # These are a modified version of Techno (still summing to 150)
    donor.stat_bonuses[TitleStatIndex.HP]  = 100 + 20
    donor.stat_bonuses[TitleStatIndex.ATK] = 100 + 20
    donor.stat_bonuses[TitleStatIndex.DEF] = 100 + 30
    donor.stat_bonuses[TitleStatIndex.INT] = 100 +  0
    donor.stat_bonuses[TitleStatIndex.RES] = 100 + 30
    donor.stat_bonuses[TitleStatIndex.SPD] = 100 + 50

    # The enemy-only Robber title's values for these:
    donor.steal = 120
    donor.move = 20


def apply_patches(arch: PSPFSArchive) -> None:
    start_dat = arch.start_dat

    add_another_marona_items_to_pools(start_dat)

    # In general these can happen in any order. The one exception is that
    # normalize_dungeon_category_rarities should happen before
    # create_rarity_category, as the latter makes a new category with a high
    # rarity which the former would overwrite.
    normalize_dungeon_category_rarities(start_dat)
    create_rarity_category(start_dat)

    maximize_fusion_compatibility(start_dat)

    adjust_skill_costs_big_time(start_dat)

    adjust_passive_skill_levels(start_dat)

    adjust_failure_title_bonuses(start_dat)

    increase_bottlemail_steal(start_dat)

    make_thief_title(start_dat)


def patch_file(src: Path, dest: Path, is_pc_or_switch: bool) -> None:
    fd = None
    try:
        fd = os.open(str(src), os.O_RDONLY)
        with mmap.mmap(fd, 0, mmap.MAP_PRIVATE) as mm:
            arch = PSPFSArchive(mm, is_pc_or_switch)
            apply_patches(arch)
            del arch  # avoiding a BufferError by triggering collection of this

            print(f'\n>> Writing output to {dest}...')
            with dest.open('wb') as output:
                output.write(mm)  # type: ignore[arg-type]
    finally:
        if fd is not None:
            os.close(fd)


def main(args: list[str]) -> int:
    if len(args) != 1 or args[0] == '-h' or args[0] == '--help':
        print('Usage: pb_mods.py <path to DATA.DAT or SUBDATA.DAT>\n', file=sys.stderr)
        print('Patched output will be created in the same directory as the input in\n'
              'a file with the suffix .patched.', file=sys.stderr)
        return 1

    src = Path(args[0])

    if not src.is_file():
        print(f'Input file {src} does not exist.')
        return 1

    if src.name == 'SUBDATA.DAT':
        is_pc_or_switch = True
    elif src.name == 'DATA.DAT':
        is_pc_or_switch = False
    else:
        print('Input file must be named either SUBDATA.DAT (PC/Switch) or DATA.DAT (PSP).',
              file=sys.stderr)
        return 1

    dest = src.with_suffix('.DAT.patched')
    if dest.exists():
        print(f'Destination {dest} already exists. Delete it and try again.')
        return 1

    patch_file(src, dest, is_pc_or_switch)
    return 0


if __name__ == '__main__':
    exit(main(sys.argv[1:]))

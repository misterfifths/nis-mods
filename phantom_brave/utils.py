from .startdatarchive import StartDatArchive
from .dungeoncategory import DungeonCategory, CategoryMemberKind
from .classoritem import ClassOrItem

__all__ = ['dump_category', 'dump_categories', 'dump_orphaned_items', 'dump_class_skills',
           'dump_all_class_skills']


"""
TODO: some sort of refrences from objects back up the hierarchy, so that e.g.
we can get from a Skill to the SkillTab it belongs to the StartDatArchive it
came from. Or maybe some sort of singleton situation?
"""


def dump_category(cat: DungeonCategory, start_dat: StartDatArchive) -> None:
    print(f'{cat.id:02x} {cat.name:<8}  monk lvl {cat.monk_level_req:<2}  rarity {cat.rarity}')

    for kind, member_id in cat.members:
        if kind == CategoryMemberKind.CATEGORY:
            cat = start_dat.cattab.category_for_id(member_id)
            print(f'  [{cat.name}]')
        else:
            coi = start_dat.classtab.entry_for_id(member_id)
            print(f'   {coi.class_name} / {coi.name}')


def dump_categories(start_dat: StartDatArchive) -> None:
    for cat in start_dat.cattab:
        dump_category(cat, start_dat)
        print()


def dump_orphaned_items(start_dat: StartDatArchive) -> None:
    # items that aren't in any categories
    orphaned_item_ids = {coi.id for coi in start_dat.classtab if coi.is_item}
    for cat in start_dat.cattab:
        for kind, member_id in cat.members:
            if kind == CategoryMemberKind.CLASS_OR_ITEM and member_id in orphaned_item_ids:
                orphaned_item_ids.remove(member_id)

    if orphaned_item_ids:
        print('Items not in any dungeon category:')
        for id in orphaned_item_ids:
            coi = start_dat.classtab.entry_for_id(id)
            print(f'  {coi.id:04x} {coi.class_name:<22} / {coi.name:<22}')


def dump_class_skills(coi: ClassOrItem, start_dat: StartDatArchive) -> None:
    print(f'{coi.id:04x} {coi.class_name}')

    for i, skill_id in enumerate(coi.passive_skill_ids):
        if skill_id == 0:
            break

        skill = start_dat.skilltab.skill_for_id(skill_id)
        lvl = coi.passive_skill_levels[i]
        print(f'  [passive] {skill_id:04x} {skill.name}, lvl {lvl}')

    for i, skill_id in enumerate(coi.active_skill_ids):
        if skill_id == 0:
            break

        skill = start_dat.skilltab.skill_for_id(skill_id)
        lvl = coi.active_skill_learn_levels[i]
        print(f'  [active]  {skill_id:04x} {skill.name}, learned @ lvl {lvl}')


def dump_all_class_skills(start_dat: StartDatArchive) -> None:
    for coi in start_dat.classtab:
        dump_class_skills(coi, start_dat)
        print()

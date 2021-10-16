from makai_kingdom.item_categories import ItemKind

from .classes import Class
from .items import Item
from .startdatarchive import StartDatArchive


def dump_class_skills(cls: Class, start_dat: StartDatArchive) -> None:
    print(f'{cls.class_name} / {cls.name}')

    for i, skill_id in enumerate(cls.passive_skill_ids):
        if skill_id == 0:
            break

        skill = start_dat.skilltab.skill_for_id(skill_id)
        lvl = cls.passive_skill_levels[i]
        print(f'  [passive] {skill_id:04x} {skill.name}, learned @ lvl {lvl}')

    for i, skill_id in enumerate(cls.active_skill_ids):
        if skill_id == 0:
            break

        skill = start_dat.skilltab.skill_for_id(skill_id)
        lvl = cls.active_skill_learn_levels[i]
        print(f'  [active]  {skill_id:04x} {skill.name}, learned @ lvl {lvl}')


def dump_item_skills(item: Item, start_dat: StartDatArchive) -> None:
    print(f'{item.id:04x} {item.name}')

    for skill_id in item.active_skill_ids:
        if skill_id == 0:
            break

        skill = start_dat.skilltab.skill_for_id(skill_id)
        lvl = skill.mastery_level
        if item.kind == ItemKind.WEAPON:
            assert item.category.mastery_skill_name  # for type-checking
            mastery_skill = start_dat.skilltab.skill_for_name(item.category.mastery_skill_name)
            print(f'  {skill_id:04x} {skill.name}, '
                  f'learned @ {mastery_skill.name} mastery level {lvl}')
        else:
            # All skills on non-weapons are available immediately (they have a
            # mastery level of 0).
            print(f'  {skill_id:04x} {skill.name}')

from .classes import Class
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

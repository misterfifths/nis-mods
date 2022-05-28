import ctypes as C
import unicodedata
from copy import deepcopy
from pathlib import Path

from makai_kingdom import *
from makai_kingdom.names import NameTable
from utils.mining import *

verbose = False

"""
Due to the hacky way I'm handling differences between PSP & PC/Switch, this
file contains all the actual patching logic for Makai Kingdom. It's imported
by the mk_mods.py, which ensures platform_config.PSP is set appropriately.
"""


def dbg(s: str) -> None:
    if verbose:
        print('   ' + s)


# The PC re-release largely uses fullwidth unicode characters for the Roman
# alphabet, which is hard to read. NFKC normalization brings them back down to
# ASCII.
def norm(s: str) -> str:
    return unicodedata.normalize('NFKC', s)


def fix_string_fields(start_dat: StartDatArchive) -> None:
    print('\n>> Fixing various misaligned strings...')

    # Mega Death has some spaces at the end of its name
    mega_death = start_dat.itemtab.item_for_name('Mega Death')
    # setting this to itself for the side-effect of zeroing bytes after the nul
    mega_death.name = mega_death.name
    dbg(f'Mega Death name: {mega_death.name!r}')
    check_null_terminated_strs(mega_death)

    # Same with Prinny Hero's class_name.
    prinny_hero = start_dat.classtab.class_for_name('Prinny Hero')
    prinny_hero.class_name = prinny_hero.class_name
    dbg(f'Prinny Hero\'s class name: {prinny_hero.class_name!r}')
    check_null_terminated_strs(prinny_hero)

    # Volcanic Blast's description begins with nulls
    volcanic_blast = start_dat.skilltab.skill_for_name('Volcanic Blast')
    fixed_desc = bytes(volcanic_blast._raw_description).lstrip(b'\0')
    # pad back up to the length of the whole field:
    fixed_desc += b'\0' * (len(volcanic_blast._raw_description) - len(fixed_desc))
    assert len(fixed_desc) == len(volcanic_blast._raw_description)
    assert fixed_desc.endswith(b'\0')
    volcanic_blast._raw_description[:] = fixed_desc
    dbg(f'Volcanic Blast description: {volcanic_blast.description!r}')
    check_null_terminated_strs(volcanic_blast)

    # A few objects have their description start early, bleeding into the end
    # of their name field, after some nulls. This function moves those bytes
    # to the beginning of the description.
    def cycle_desc_from_name(o: C.Structure) -> None:
        name_bytes, desc_bytes = bytearray(o._raw_name).split(b'\0', 1)

        # pad back to the length of the whole field
        name_bytes += b'\0' * (len(o._raw_name) - len(name_bytes))
        assert len(name_bytes) == len(o._raw_name)
        assert name_bytes.endswith(b'\0')
        o._raw_name[:] = name_bytes

        # build the new description starting with what was at the end of name
        desc_bytes.extend(bytes(o._raw_description))
        desc_bytes = desc_bytes.strip(b'\0')
        desc_bytes += b'\0' * (len(o._raw_description) - len(desc_bytes))
        assert len(desc_bytes) == len(o._raw_description)
        assert desc_bytes.endswith(b'\0')
        o._raw_description[:] = desc_bytes

    bad_name_skills = ('Heart Breaker', 'Arc Fire', 'Hero Stunt', 'Bomb Crush')
    for skill_name in bad_name_skills:
        skill = start_dat.skilltab.skill_for_name(skill_name)
        cycle_desc_from_name(skill)
        dbg(f'{skill.name} description: {skill.description!r}')
        check_null_terminated_strs(skill)

    # Asagi's description also starts at the end of the name.
    asagi = start_dat.classtab.class_for_class_name('Asagi')
    cycle_desc_from_name(asagi)
    dbg(f'Asagi\'s description: {asagi.description!r}')
    check_null_terminated_strs(asagi)


def unpad_names(start_dat: StartDatArchive) -> NameTable:
    print('\n>> Removing padding from names...')

    # Not sure if this is strictly necessary, but I have a hunch that some of
    # the names in the translated name table overflow the field on the class
    # structure.

    trimmed_name_lists = deepcopy(start_dat.nametab.name_lists)
    for type_list in trimmed_name_lists:
        for i, name in enumerate(type_list):
            type_list[i] = name.rstrip(' \u3000')

    return NameTable.from_names(trimmed_name_lists)


def adjust_building_capacity(start_dat: StartDatArchive) -> None:
    print('\n>> Increasing building capacity...')

    for bldg in start_dat.classtab:
        if not bldg.is_building:
            continue

        assert bldg.total_slots == bldg.character_slots
        new_capacity = min(16, bldg.total_slots * 2)

        if new_capacity != bldg.total_slots:
            dbg(f'{norm(bldg.name)}: {bldg.total_slots} -> {new_capacity}')
            bldg.total_slots = bldg.character_slots = new_capacity


def adjust_wish_reqs(start_dat: StartDatArchive) -> None:
    print('\n>> Lowering wish mana costs and level requirements...')

    for wish in start_dat.wishtab:
        new_cost = wish.mana_cost // 10
        if wish.mana_cost > 0 and new_cost == 0:
            new_cost = 1

        new_cost = min(1000, new_cost)

        new_lvl_req = wish.level_req // 3
        if wish.level_req > 0 and new_lvl_req == 0:
            new_lvl_req = 1

        new_lvl_req = min(100, new_lvl_req)

        if new_cost != wish.mana_cost or new_lvl_req != wish.level_req:
            dbg(f'{norm(wish.name)!r} mana {wish.mana_cost} -> {new_cost}, '
                f'level {wish.level_req} -> {new_lvl_req}')
            wish.mana_cost = new_cost
            wish.level_req = new_lvl_req


def lower_character_creation_costs(start_dat: StartDatArchive) -> None:
    print('\n>> Lowering character mana costs...')

    for cls in start_dat.classtab:
        if not cls.is_generic_character:
            continue

        new_cost = cls.mana_cost // 10
        if cls.mana_cost > 0 and new_cost == 0:
            new_cost = 1

        if new_cost != cls.mana_cost:
            dbg(f'{norm(cls.name)}: {cls.mana_cost} -> {new_cost}')
            cls.mana_cost = new_cost


def boost_kill_bonuses(start_dat: StartDatArchive) -> None:
    print('\n>> Raising EXP/HL/mana kill bonuses on all classes...')

    for cls in start_dat.classtab:
        cls.hl_bonus = cls.exp_bonus = cls.mana_bonus = 150


def lower_passive_learn_levels(start_dat: StartDatArchive) -> None:
    print('\n>> Lowering passive skill learn levels...')

    for cls in start_dat.classtab:
        if not cls.is_generic_character:
            continue

        for i, skill_id in enumerate(cls.passive_skill_ids):
            if skill_id == 0:
                break

            skill = start_dat.skilltab.skill_for_id(skill_id)
            if skill.kind != SkillKind.PASSIVE:
                continue

            old_learn_level = cls.passive_skill_learn_levels[i]
            if old_learn_level > 1:
                new_learn_level = max(1, old_learn_level // 2)
                if new_learn_level != old_learn_level:
                    dbg(f'{norm(cls.name)}: {norm(skill.name)} @ lvl {old_learn_level} -> '
                        f'{new_learn_level}')
                    cls.passive_skill_learn_levels[i] = new_learn_level


def lower_building_mana_costs(start_dat: StartDatArchive) -> None:
    print('\n>> Zeroing building mana costs...')

    for cls in start_dat.classtab:
        if not cls.is_building:
            continue

        # The formula that calculates mana costs for buildings is pretty
        # outrageous; even if we reduce all the base costs to 1, they still
        # grow exponentially with the level of the character making the wish.
        # I don't feel awful just setting them to zero since there's already
        # the added cost of sacrificing a character.
        cls.mana_cost = 0


def more_things_for_sale(start_dat: StartDatArchive) -> None:
    print('\n>> Making more items available for purchase...')

    BUYABLE_CATEGORIES = (ItemCategory.SHOES,
                          ItemCategory.GLASSES,
                          ItemCategory.BELT,
                          ItemCategory.RING)

    for i in start_dat.itemtab:
        # Only making the rarity 1 items buyable. That keeps the top-tier items
        # in these categories only available in dungeons.
        if i.rarity == 1 and i.category in BUYABLE_CATEGORIES:
            dbg(norm(i.name))
            i.rarity = 0

    gency_tonic = start_dat.itemtab.item_for_name('Gency Tonic')
    gency_tonic.rarity = 0
    gency_tonic.hl_cost = 1000  # up from 500
    # The shops have some sort of filter for which items they'll list, and
    # Travel Items are excluded. Changing the category was the only way I could
    # find to have it appear. Treasure was just an arbitrary choice. This
    # doesn't seem to have any other side effects, other than changing its sort
    # order.
    gency_tonic.category = ItemCategory.TREASURE
    dbg(norm(gency_tonic.name))


def apply_psp_translation_fixes(start_dat: StartDatArchive) -> StartDatArchive:
    updated_nametab = unpad_names(start_dat)
    start_dat = start_dat.archive_by_replacing_file(NameTable.STANDARD_FILENAME,
                                                    updated_nametab._buffer)  # type: ignore

    fix_string_fields(start_dat)

    return start_dat


def apply_mods(start_dat: StartDatArchive) -> None:
    adjust_building_capacity(start_dat)
    adjust_wish_reqs(start_dat)
    lower_character_creation_costs(start_dat)
    boost_kill_bonuses(start_dat)
    lower_passive_learn_levels(start_dat)
    lower_building_mana_costs(start_dat)
    more_things_for_sale(start_dat)


'''
On the PSP, there's a DATA.DAT file that is an archive of the majority of the
game's assets (animations, sprites, levels, etc.). It's in the PSPFS format,
handled by the PSPFSArchive class. The main file we care about in DATA.DAT is
START.KS4, which is yet another archive. It's in YKCMP format, handled by the
YKCMPArchive class. START.KS4 contains most of the raw data we'd like to
manipulate (item and class stats, skill information, etc.). So for PSP mods,
our gameplan is to extract START.KS4 from DATA.DAT, unarchive it, change what
we want to change, recompress it, and repack DATA.DAT with the new START.KS4.

For the PC and Switch re-release, the DATA.DAT file does not exist, and is
unpacked onto the filesystem. That means we can just decompress the start.ks4
file (lowercase this time) directly and recompress it when we're done.
'''


def patch_start_dat(start_dat: StartDatArchive, is_psp: bool) -> YKCMPArchive:
    if is_psp:
        apply_psp_translation_fixes(start_dat)

    apply_mods(start_dat)

    print('\n>> Compressing new START.DAT...')
    return YKCMPArchive.compress(start_dat._buffer)  # type: ignore


def patch_start_ks4(src: Path, dest: Path) -> None:
    print(f'>> Opening {src} (PC/Switch)')
    with YKCMPArchive.from_file(src) as start_arch:
        start_dat_buf = start_arch.decompress()
        start_dat = StartDatArchive(start_dat_buf)

        compressed_start_dat = patch_start_dat(start_dat, is_psp=False)

        print(f'\n>> Writing output to {dest}...')
        with dest.open('wb') as output:
            output.write(compressed_start_dat._buffer)  # type: ignore


def patch_data_dat(src: Path, dest: Path) -> None:
    print(f'>> Opening {src} (PSP)')
    with PSPFSArchive.from_file(src) as arch:
        start_dat = arch.get_start_dat()
        compressed_start_dat = patch_start_dat(start_dat, is_psp=True)

        print('\n>> Generating new DATA.DAT...')
        arch = arch.archive_by_replacing_file(StartDatArchive.STANDARD_FILENAME,
                                              compressed_start_dat._buffer)  # type: ignore

        print(f'\n>> Writing output to {dest}...')
        with dest.open('wb') as output:
            output.write(arch._buffer)  # type: ignore

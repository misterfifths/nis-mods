#!/usr/bin/env python3

import sys
from pathlib import Path
from typing import Optional


def main(args: list[str]) -> int:
    is_psp: Optional[bool] = None
    if '-psp' in args:
        is_psp = True
        args.remove('-psp')

    verbose = False
    if '-v' in args:
        verbose = True
        args.remove('-v')

    force = False
    if '-f' in args:
        force = True
        args.remove('-f')

    if len(args) != 1 or args[0] == '-h' or args[0] == '--help':
        print('Usage: mk_mods.py [-v] [-f] <path to DATA.DAT or start.ks4>\n', file=sys.stderr)
        print('If the input file is named DATA.DAT, it is assumed to be for the PSP\n'
              'version of the game. Otherwise, it is assumed to be for the PC or\n'
              'Switch versions of the game (which use start.ks4). Provide the\n'
              '-psp argument to force that mode regardless of the filename.\n', file=sys.stderr)
        print('Patched output will be created in the same directory as the input in\n'
              'a file with the suffix .patched.\n', file=sys.stderr)
        print('-v    Verbose logging', file=sys.stderr)
        print('-f    Overwrite an existing output file', file=sys.stderr)
        print('-psp  Process the input in PSP mode', file=sys.stderr)
        return 1

    src = Path(args[0])

    if not src.is_file():
        print(f'Input file {src} does not exist.')
        return 1

    if is_psp is None:
        if src.name == 'DATA.DAT':
            is_psp = True
        else:
            is_psp = False
            if src.name != 'start.ks4':
                print('>> Assuming the input is for the PC or Switch version of the game!\n')

    if src.suffix == '.DAT':
        dest = src.with_suffix('.DAT.patched')
    elif src.suffix == '.ks4':
        dest = src.with_suffix('.ks4.patched')
    else:
        dest = src.with_suffix('.patched')

    if dest.exists() and not force:
        print(f'Destination {dest} already exists. Delete it and try again.')
        return 1

    # We need to update platform_config before importing any makai_kingdom
    # stuff. To make that easy, all the actual work of this patcher is in the
    # mk_mods_guts.py file.
    import platform_config as pc
    pc.PSP = is_psp

    import mk_mods_guts as guts
    guts.verbose = verbose

    if is_psp:
        guts.patch_data_dat(src, dest)
    else:
        guts.patch_start_ks4(src, dest)

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

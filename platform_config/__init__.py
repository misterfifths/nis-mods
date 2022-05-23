"""
This module is used in a hacky way to account for differences in structures
between the PSP and the PC/Switch versions of the games. At the moment it is
only required for Makai Kingdom, since the differences there were the most
substantial.

This module should be imported and the value of the PSP variable should be
changed appropriately before anything from the makai_kingdom module is
imported.
"""

PSP = True

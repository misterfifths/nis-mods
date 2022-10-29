from phantom_brave.startdatarchive import StartDatBase
from utils import ro_cached_property

from .items import ItemTable
from .ritems import RItemTable
from .skills import SkillTable


# La Pucelle's start_{en,jp}.dat format is the same as Phantom Brave's. The
# shared details are in StartDatBase.
class StartDatArchive(StartDatBase):
    STANDARD_PATH = 'PSP_GAME/USRDIR/start_en.dat'

    @ro_cached_property
    def itemtab(self) -> ItemTable:
        file_entry = self.find_file(ItemTable.STANDARD_FILENAME)
        return ItemTable(self._buffer, file_entry.offset)

    @ro_cached_property
    def ritemtab(self) -> RItemTable:
        file_entry = self.find_file(RItemTable.STANDARD_FILENAME)
        return RItemTable(self._buffer, file_entry.offset)

    @ro_cached_property
    def skilltab(self) -> SkillTable:
        file_entry = self.find_file(SkillTable.STANDARD_FILENAME)
        return SkillTable(self._buffer, file_entry.offset)

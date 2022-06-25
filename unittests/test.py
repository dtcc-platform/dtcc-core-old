import unittest

import sys
from pathlib import Path

sys.path.append( str((Path(__file__).parent / "../src").resolve() ))
from dtcc import cityModel

class TestBuildings(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.building_shp_file = str((Path(__file__).parent / "data" / "MinimalCase" / "propertyMap.shp").resolve())

    def test_load_shp_buildings(self):
        cm = cityModel.LoadBuildings(self.building_shp_file,'uuid')
        self.assertEqual(len(cm.buildings),5)

if __name__ == '__main__':
    unittest.main()
"""Regression checks for the signal shapes exported from library documentation.

Run with: python3 -m unittest discover -s tests -p test_doc_index.py
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from build_faust_doc_index import parse_usage_io


class UsageShapeTests(unittest.TestCase):
    def test_waveguide_bus_shapes(self):
        cases = {
            "si.bus(144), _, si.bus(44), si.bus(46) : tractTick : si.bus(144)": (235, 144),
            "si.bus(44), _ : tractReflections : si.bus(46)": (45, 46),
            "tractDiameters(ti, td, ci, cd, ca) : si.bus(44)": (None, 44),
            "bus( 2 ), _ : processor : bus(3), !": (3, 3),
        }
        for usage, expected in cases.items():
            with self.subTest(usage=usage):
                io = parse_usage_io(usage)
                self.assertEqual((io["inSignals"], io["outSignals"]), expected)

    def test_existing_scalar_shapes(self):
        cases = {
            "_ : filter : _": (1, 1),
            "_, _ : effect : _, _, _": (2, 3),
            "simplex2(seed, x, y) : _": (None, 1),
            None: (None, None),
        }
        for usage, expected in cases.items():
            with self.subTest(usage=usage):
                io = parse_usage_io(usage)
                self.assertEqual((io["inSignals"], io["outSignals"]), expected)


if __name__ == "__main__":
    unittest.main()

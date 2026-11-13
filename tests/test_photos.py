import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from pipeline import photos


class PhotoTests(unittest.TestCase):
    def test_bearing_north_east(self):
        self.assertAlmostEqual(photos.bearing(0, 0, 1, 0), 0, delta=1)
        self.assertAlmostEqual(photos.bearing(0, 0, 0, 1), 90, delta=1)

    def test_pick_best_prefers_facing_and_near(self):
        lat, lon = -23.55, -46.63
        south = {"id": "s", "captured_at": 1, "computed_compass_angle": 0, "computed_geometry": {"coordinates": [lon, lat - 0.0002]}}  # ~22 m ao sul olhando p/ norte
        away = {"id": "a", "captured_at": 2, "computed_compass_angle": 180, "computed_geometry": {"coordinates": [lon, lat - 0.0001]}}  # olhando para longe
        far = {"id": "f", "captured_at": 3, "computed_compass_angle": 0, "computed_geometry": {"coordinates": [lon, lat - 0.002]}}  # ~220 m
        self.assertEqual(photos.pick_best([away, far, south], lat, lon)["id"], "s")
        self.assertIsNone(photos.pick_best([away, far], lat, lon))

    def test_manual_requires_credit_and_license(self):
        with self.assertRaises(ValueError):
            photos.add_manual("r1", "x.jpg", "", "")

    def test_manual_writes_manifest(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "f.jpg"
            src.write_bytes(b"x")
            with mock.patch.object(photos, "PHOTOS_DIR", Path(d) / "out"), mock.patch.object(photos, "MANIFEST", Path(d) / "m.json"):
                photos.add_manual("r1", str(src), "Foto: Restaurante X", "autorização do restaurante")
                m = json.loads((Path(d) / "m.json").read_text())
        self.assertEqual(m["r1"]["license"], "autorização do restaurante")

    def test_mapillary_blocked_without_token(self):
        with mock.patch.dict("os.environ", {}, clear=True):
            self.assertEqual(photos.fetch_mapillary([])["status"], "blocked_no_token")


if __name__ == "__main__":
    unittest.main()

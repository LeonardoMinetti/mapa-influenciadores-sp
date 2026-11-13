"""Valida os arquivos públicos gerados (dados REAIS desta execução)."""
import json
import re
import unittest
from pathlib import Path

PUB = Path(__file__).resolve().parent.parent / "data" / "public"
FORBIDDEN_KEYS = {"snippet", "caption", "text", "author", "username", "comment", "comments"}


def walk(o):
    if isinstance(o, dict):
        for k, v in o.items():
            yield k
            yield from walk(v)
    elif isinstance(o, list):
        for i in o:
            yield from walk(i)


class DataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.posts = json.loads((PUB / "posts.json").read_text())
        cls.rests = json.loads((PUB / "restaurants.json").read_text())
        cls.infl = json.loads((PUB / "influencers.json").read_text())

    def test_only_three_influencers(self):
        self.assertEqual({i["handle"] for i in self.infl}, {"reviewsporsp", "incrivelsp", "vivamaissp"})

    def test_post_urls_match_handle(self):
        for p in self.posts:
            self.assertRegex(p["url"], rf"^https://www\.tiktok\.com/@{p['influencer']}/video/{p['post_id']}$")

    def test_referential_integrity(self):
        rid = {r["restaurant_id"] for r in self.rests}
        pid = {p["post_id"] for p in self.posts}
        for p in self.posts:
            self.assertTrue(set(p["restaurant_ids"]) <= rid)
        for r in self.rests:
            self.assertTrue(set(r["post_ids"]) <= pid)

    def test_coordinates_have_quality_and_are_in_brazil(self):
        for r in self.rests:
            if r["lat"] is not None:
                self.assertIn(r["coordinate_quality"], {"address_exact", "street_approx", "area"})
                self.assertTrue(-34 < r["lat"] < 6 and -74 < r["lon"] < -34)
            else:
                self.assertEqual(r["coordinate_quality"], "none")

    def test_unverified_never_auto_ok_without_exact_address(self):
        for r in self.rests:
            if r["review_status"] == "auto_ok":
                self.assertEqual(r["coordinate_quality"], "address_exact")

    def test_no_third_party_text_or_personal_data_in_public_json(self):
        for name in ("posts", "restaurants", "influencers"):
            data = json.loads((PUB / f"{name}.json").read_text())
            self.assertFalse(FORBIDDEN_KEYS & set(walk(data)), name)

    def test_ad_flag_wording(self):
        for p in self.posts:
            self.assertIn(p["ad_disclosure"], {"declared", "not_detected_in_available_text"})


if __name__ == "__main__":
    unittest.main()

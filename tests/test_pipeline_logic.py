import os
import unittest
from unittest import mock

from pipeline import consolidate, crosscheck, geocode, google_places
from pipeline.collect_tiktok import date_from_video_id


class ConsolidateTests(unittest.TestCase):
    def setUp(self):
        self.seeds = [
            {"handle": "incrivelsp", "post_id": "1", "url": "u1"},
            {"handle": "incrivelsp", "post_id": "2", "url": "u2"},
            {"handle": "vivamaissp", "post_id": "3", "url": "u3"},
            {"handle": "vivamaissp", "post_id": "4", "url": "u4"},
        ]
        self.snips = {
            "1": {"snippet": "Voltamos na @pizzariamammaconcetta amamos 📍Rua Prof Pedreira de Freitas, 629 - Tatuape"},
            "2": {"snippet": "Conhecemos @pizzeriamammaconcetta incrível 📍R. Prof. Pedreira de Freitas, 629 - Tatuapé"},
            "3": {"snippet": "@redex amamos 📍MOEMA - Av. A, 10📍ALPHAVILLE - Av. B, 20"},
            "4": {"snippet": "Texto só com #hashtag e nada de restaurante"},
        }
        self.ann = {"display_names_by_handle": {"pizzariamammaconcetta": "Mamma Concetta",
                                                "pizzeriamammaconcetta": "Mamma Concetta", "redex": "Rede X"},
                    "post_overrides": {}, "post_notes": {}}

    def test_duplicates_merge_and_units_split(self):
        posts, rests, links = consolidate.consolidate(self.seeds, self.snips, self.ann)
        mamma = [r for r in rests if r["name"] == "Mamma Concetta"]
        self.assertEqual(len(mamma), 1)
        self.assertEqual(len(mamma[0]["post_ids"]), 2)
        redex = [r for r in rests if r["name"] == "Rede X"]
        self.assertEqual(len(redex), 2)
        self.assertTrue(all(r["multi_unit_brand"] for r in redex))

    def test_post_without_restaurant_is_pending(self):
        posts, _, _ = consolidate.consolidate(self.seeds, self.snips, self.ann)
        p4 = [p for p in posts if p["post_id"] == "4"][0]
        self.assertEqual(p4["restaurant_ids"], [])
        self.assertEqual(p4["review_status"], "pending_review")

    def test_date_from_id(self):
        self.assertEqual(date_from_video_id("7405595760361737477"), "2024-08-21")


class GeocodeTests(unittest.TestCase):
    def test_rejects_other_municipality(self):
        fake = [{"lat": "-23.2", "lon": "-45.9", "osm_type": "way", "osm_id": 1, "category": "highway", "type": "secondary",
                 "display_name": "x", "address": {"city": "São José dos Campos"}}]
        with mock.patch.object(geocode, "_search", return_value=fake):
            r = geocode.geocode_restaurant("X", "Avenida do Imperador, 4424", None)
        self.assertEqual(r["status"], "municipality_mismatch")
        self.assertIsNone(r["lat"])

    def test_no_number_is_never_exact(self):
        fake = [{"lat": "-23.0", "lon": "-46.0", "osm_type": "node", "osm_id": 2, "category": "place", "type": "house",
                 "display_name": "x", "address": {"city": "Atibaia", "house_number": "1"}}]
        with mock.patch.object(geocode, "_search", return_value=fake):
            r = geocode.geocode_restaurant("X", "Rua 20 de novembro, sem número - atibaia - sp", "Atibaia")
        self.assertEqual(r["coordinate_quality"], "street_approx")

    def test_simplify(self):
        self.assertEqual(geocode.simplify_address("Rua Gen. Calado, 20 - Tatuapé", "São Paulo"), "Rua General Calado, 20, São Paulo")


class GoogleTests(unittest.TestCase):
    def test_blocked_without_key(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(google_places.fetch_place("A", "B")["status"], "blocked_no_api_key")

    def test_blocked_without_billing_authorization(self):
        with mock.patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "k"}):
            self.assertEqual(google_places.fetch_place("A", "B")["status"], "blocked_billing_not_authorized")

    def test_themes(self):
        t = google_places.tag_themes("Atendimento demorado, mas a comida é ótima e o ambiente é lindo")
        for x in ("atendimento", "tempo_espera", "comida", "ambiente"):
            self.assertIn(x, t)


class CrosscheckTests(unittest.TestCase):
    def test_missing_sources_reported(self):
        r = crosscheck.build({"restaurant_id": "r", "post_ids": ["p"]}, {"p": "ótimo atendimento"}, [], None)
        self.assertEqual(r["status"], "insufficient_sources")
        self.assertIn("audience", r["missing"])
        self.assertEqual(r["hypotheses"], [])

    def test_hypothesis_is_not_a_conclusion(self):
        cms = [{"post_id": "p", "labels": ["critica_atendimento"], "confidence": "medium"}]
        r = crosscheck.build({"restaurant_id": "r", "post_ids": ["p"]}, {"p": "atendimento rápido"}, cms,
                             {"status": "ok", "theme_counts": {"atendimento": 1}})
        self.assertEqual(r["status"], "cross_analysis_possible")
        h = r["hypotheses"][0]["text"]
        self.assertIn("Hipótese", h)
        self.assertNotIn("mentiu", h.lower())


if __name__ == "__main__":
    unittest.main()

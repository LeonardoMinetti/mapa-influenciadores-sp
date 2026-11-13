import unittest

from pipeline.extract import detect_ad, extract, normalize_address


class ExtractTests(unittest.TestCase):
    def test_pin_with_name_and_address(self):
        e = extract("Vocês pediriam? 📍Legado Parrilla - R. Mal. Barbacena, 555 - Vila Reg. Feijó, São Paulo #picanha")
        self.assertEqual(e["venue_name"], "Legado Parrilla")
        self.assertIn("555", e["address_text"])

    def test_handle_and_address(self):
        e = extract("Conhecemos o @carola.restobar e amamos! 📍Rua Fernando de Albuquerque, 77 - Consolação")
        self.assertEqual(e["venue_handle"], "carola.restobar")
        self.assertEqual(e["recommendation_type"], "recommendation")
        self.assertEqual(e["confidence"], "high")

    def test_hashtags_never_become_restaurant_names(self):
        e = extract("Eu sou apaixonada nesse lugar #restaurante #camarão #comeremsp")
        self.assertIsNone(e["venue_name"])
        self.assertEqual(e["recommendation_type"], "unknown")
        self.assertEqual(e["review_status"], "pending_review")

    def test_credit_handle_is_not_venue(self):
        e = extract("Olha esse bar @sealounge.sp 📍 Praia de Pitangueiras 🎥 @gabriel_limaa26")
        self.assertEqual(e["venue_handle"], "sealounge.sp")

    def test_unit_label_kept_for_chains(self):
        e = extract("🍔@cromaburguers📍CARRÃO - Av. Guilherme Giorgi, 417📍OSASCO - Av. Santo Antônio, 1719💳 Aceitam VR")
        self.assertEqual(e["venue_handle"], "cromaburguers")
        self.assertTrue(e["address_text"].startswith("CARRÃO"))
        self.assertTrue(e["extra_unit_addresses"][0].startswith("OSASCO"))

    def test_ad_detection_and_absence_wording(self):
        self.assertEqual(detect_ad("ótimo lugar *Publi #sp"), "declared")
        self.assertEqual(detect_ad("• publi"), "declared")
        # ausência de marcação NUNCA vira "sem publicidade"
        self.assertEqual(detect_ad("ótimo lugar"), "not_detected_in_available_text")

    def test_normalize_address_merges_variants(self):
        a = normalize_address("Rua Prof Pedreira de Freitas, 629 - Tatuape, São Paulo")
        b = normalize_address("R. Prof. Pedreira de Freitas, 629 - Tatuapé")
        self.assertEqual(a, b)

    def test_mention_only_vs_visit(self):
        self.assertEqual(extract("Fomos no @lugar 📍Rua A, 10 - Moema")["recommendation_type"], "visit_showcase")
        self.assertEqual(extract("O @lugar 📍Rua A, 10 - Moema")["recommendation_type"], "mention_only")


if __name__ == "__main__":
    unittest.main()

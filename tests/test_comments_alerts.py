import csv
import tempfile
import unittest
from pathlib import Path

from pipeline import alerts
from pipeline.comments import classify, import_comments_csv, scrub


def C(text, pid="p1"):
    return {"post_id": pid, "text": text, **classify(text)}


class CommentTests(unittest.TestCase):
    def test_multi_label(self):
        labels = classify("Amei! Onde fica? Vou ir semana que vem")["labels"]
        for l in ("elogio", "duvida_localizacao_funcionamento", "intencao_visita"):
            self.assertIn(l, labels)

    def test_other_is_low_confidence(self):
        r = classify("🔥🔥🔥")
        self.assertEqual(r["labels"], ["outros"])
        self.assertEqual(r["confidence"], "low")

    def test_scrub_pii(self):
        t = scrub("fala com @fulano ou fulano@x.com ou (11) 91234-5678")
        self.assertNotIn("fulano@x.com", t)
        self.assertNotIn("91234", t)
        self.assertNotIn("@fulano", t)

    def test_import_drops_author_and_caps(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "comments_x.csv"
            with open(p, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["post_id", "author", "text", "source", "collected_on", "method"])
                for i in range(40):
                    w.writerow(["p1", "usuario_secreto", f"Amei {i}", "manual", "2026-11-13", "primeiros"])
            rows = import_comments_csv(p, max_per_post=30)
        self.assertEqual(len(rows), 30)
        self.assertTrue(all("author" not in r and "usuario_secreto" not in str(r) for r in rows))


class AlertTests(unittest.TestCase):
    def test_insufficient(self):
        self.assertEqual(alerts.evaluate([C("Isso é publi, parece propaganda")] * 3)["state"], "insufficient_data")

    def test_no_signals(self):
        cm = [C("Amei demais")] * 12
        self.assertEqual(alerts.evaluate(cm)["state"], "no_relevant_signals")

    def test_ad_only_never_alerts(self):
        # comentários que apenas mencionam parceria de forma neutra (1 pista => confiança baixa) não disparam
        cm = [C("Que bom, parceria com o chef")] * 12
        self.assertEqual(alerts.evaluate(cm)["state"], "no_relevant_signals")

    def test_recurring(self):
        cm = [C("Isso é publi? Propaganda disfarçada", "p1"), C("Parece fake, foi pago pra falar bem", "p2"),
              C("Mentira, tudo combinado, não confio", "p2")] + [C("Amei")] * 9
        r = alerts.evaluate(cm)
        self.assertEqual(r["state"], "recurring_questions")
        self.assertTrue(r["evidence_examples"] and r["limitations"] and r["suggestions"])

    def test_attention(self):
        cm = [C("Isso é publi? Propaganda disfarçada")] + [C("Amei")] * 11
        self.assertEqual(alerts.evaluate(cm)["state"], "attention")


if __name__ == "__main__":
    unittest.main()

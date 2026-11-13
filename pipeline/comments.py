"""Social listening: classificação multi-rótulo de comentários + importação com minimização de dados.

Coleta automática de comentários NÃO é feita (TikTok: só Research API acadêmica; Instagram: só Graph
API com autorização do dono da conta). Este módulo recebe comentários obtidos legitimamente via
CSV (`data/imports/comments_*.csv`) e os classifica por regras (léxico PT-BR) — baseline auditável.

Privacidade: nomes/usuários NÃO são lidos nem armazenados; @menções, e-mails e telefones são
removidos do texto antes de qualquer uso. Comentário de espectador NÃO é avaliação de cliente.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

from .extract import strip_accents

LABELS = [
    "elogio", "critica_comida", "critica_atendimento", "questiona_preco", "duvida_localizacao_funcionamento",
    "intencao_visita", "relato_visita_anterior", "questiona_publicidade", "questiona_autenticidade", "outros",
]

LEX = {
    "elogio": ["amo", "amei", "delicia", "maravilh", "perfeit", "incrivel", "top", "lindo", "show", "melhor",
               "parabens", "uau", "apaixonad", "demais"],
    "critica_comida": ["comida fria", "sem sabor", "sem gosto", "salgad", "passou do ponto", "comida ruim", "horrivel",
                       "decepcion", "caro pelo que", "porcao pequena", "mal passad", "cabelo"],
    "critica_atendimento": ["atendimento ruim", "garcom", "demorou", "demora", "mal atendid", "grosseir",
                            "fomos mal", "pessimo atendimento", "esperamos"],
    "questiona_preco": ["caro", "preco", "valor", "quanto custa", "quanto e", "barato", "cobram", "r$"],
    "duvida_localizacao_funcionamento": ["onde fica", "endereco", "horario", "abre", "fecha", "aceita", "reserva",
                                         "tem estacionamento", "qual unidade", "funciona", "ainda existe", "localizacao"],
    "intencao_visita": ["vou ir", "quero ir", "preciso ir", "vamos ir", "marca", "bora", "vou la", "anotado",
                        "salvei", "quero conhecer", "me leva"],
    "relato_visita_anterior": ["fui", "fomos", "ja fui", "ja fomos", "estive", "jantei", "almocei", "visitei",
                               "voltei", "frequento"],
    "questiona_publicidade": ["publi", "publicidade", "patrocin", "pago pra", "paga pra", "parceria", "recebido",
                              "foi pago", "propaganda"],
    "questiona_autenticidade": ["fake", "mentira", "enganad", "nao e isso tudo", "nao eh isso", "nao e assim",
                                "foto enganosa", "so fala bem", "tudo e bom", "nunca fala mal", "nao confio",
                                "nao acredito", "combinado", "roteiro"],
}

PII_RE = [
    (re.compile(r"@[\w.]+"), "@usuario"),
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), "[email]"),
    (re.compile(r"\+?\d[\d\s().-]{8,}\d"), "[telefone]"),
]


def scrub(text: str) -> str:
    # e-mail antes de @menção
    text = PII_RE[1][0].sub(PII_RE[1][1], text)
    text = PII_RE[0][0].sub(PII_RE[0][1], text)
    text = PII_RE[2][0].sub(PII_RE[2][1], text)
    return text.strip()


def classify(text: str) -> dict:
    """Retorna rótulos (múltiplos) e confiança. confiança ~ nº de pistas / 'outros' => baixa."""
    low = strip_accents(text.lower())
    hits = {}
    for label, cues in LEX.items():
        n = sum(1 for c in cues if re.search(r"(?<![a-z])" + re.escape(c), low))
        if n:
            hits[label] = n
    labels = sorted(hits) or ["outros"]
    total = sum(hits.values())
    conf = "low" if labels == ["outros"] else ("high" if total >= 3 else "medium" if total == 2 else "low")
    return {"labels": labels, "cue_hits": hits, "confidence": conf, "method": "lexicon_rules_v1"}


def import_comments_csv(path: Path, max_per_post: int = 30) -> list[dict]:
    """Colunas aceitas: post_id, text, source, collected_on, method, platform_total_comments (opcional).
    Colunas de autor/usuário são IGNORADAS de propósito."""
    out, per_post = [], {}
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            pid = (r.get("post_id") or "").strip()
            if not pid or not (r.get("text") or "").strip():
                continue
            if per_post.get(pid, 0) >= max_per_post:
                continue
            per_post[pid] = per_post.get(pid, 0) + 1
            clean = scrub(r["text"])
            c = classify(clean)
            out.append({
                "post_id": pid, "text": clean, "source": r.get("source", "import"),
                "collected_on": r.get("collected_on", ""), "selection_method": r.get("method", "unspecified"),
                "platform_total_comments": r.get("platform_total_comments") or None, **c,
            })
    return out

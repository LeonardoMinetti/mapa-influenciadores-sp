"""Cruzamento das três perspectivas (promessa × audiência × clientes) por restaurante.

Gera HIPÓTESES de investigação com contagens e origem das evidências. Nunca conclui que o
influenciador mentiu ou que a recomendação foi inautêntica. Fonte ausente => reportada como ausência.
"""
from __future__ import annotations

from .extract import strip_accents
import re

PROMISE_CUES = {
    "comida": ["comida", "prato", "sabor", "massa", "carne", "rodizio", "cardapio", "pizza", "burger", "hamburguer", "sushi"],
    "atendimento": ["atendimento", "garcom", "equipe"],
    "tempo_espera": ["rapido", "rapidez", "sem fila", "sem espera"],
    "preco_custo_beneficio": ["preco", "custo-beneficio", "a partir de", "r$", "💲", "barato", "promocao", "valor"],
    "ambiente": ["ambiente", "rooftop", "vista", "decoracao", "tematic", "lindo", "romantico"],
    "experiencia_geral": ["melhor", "incrivel", "amamos", "perfeit", "favorit"],
}
AUDIENCE_LABEL_TO_THEME = {
    "elogio": "experiencia_geral", "critica_comida": "comida", "critica_atendimento": "atendimento",
    "questiona_preco": "preco_custo_beneficio",
}


def promise_themes(text: str) -> list[str]:
    low = strip_accents(text.lower())
    return [t for t, cues in PROMISE_CUES.items() if any(strip_accents(c) in low for c in cues)]


def build(restaurant: dict, post_texts: dict, comments: list[dict], google: dict | None) -> dict:
    """post_texts: {post_id: texto} (apenas em memória). comments: comentários analisados do restaurante."""
    promise = {}
    for pid in restaurant["post_ids"]:
        for t in promise_themes(post_texts.get(pid, "")):
            promise.setdefault(t, []).append(pid)
    audience: dict = {}
    for c in comments:
        for lab in c.get("labels", []):
            th = AUDIENCE_LABEL_TO_THEME.get(lab)
            if th:
                audience[th] = audience.get(th, 0) + 1
    customers = (google or {}).get("theme_counts") if (google or {}).get("status") == "ok" else None
    sources_available = {"promise": bool(promise), "audience": bool(comments), "customers_google": customers is not None}
    n_src = sum(sources_available.values())
    out = {
        "restaurant_id": restaurant["restaurant_id"], "sources_available": sources_available,
        "promise_themes": {k: len(v) for k, v in promise.items()},
        "audience_theme_counts": audience, "customer_theme_counts": customers,
        "comments_analyzed": len(comments), "hypotheses": [],
        "status": "cross_analysis_possible" if n_src >= 3 else ("partial_two_sources" if n_src == 2 else "insufficient_sources"),
        "missing": [k for k, v in sources_available.items() if not v],
    }
    # hipótese apenas quando há duas perspectivas com evidência sobre o mesmo tema
    for th, pids in promise.items():
        a = audience.get(th, 0)
        c = (customers or {}).get(th, 0)
        if a or c:
            out["hypotheses"].append({
                "theme": th, "promise_posts": len(pids), "audience_mentions": a, "customer_mentions": c,
                "text": (f"Hipótese de investigação (não conclusão): o tema '{th}' foi destacado em {len(pids)} publicação(ões) "
                         f"e aparece em {a} comentário(s) da audiência e {c} avaliação(ões) de clientes selecionadas. "
                         "Verificar manualmente antes de qualquer interpretação."),
            })
    return out

"""Módulo Google (Places API New) — preparado, com travas de custo e de termos.

Estado desta PoC: SEM chave de API configurada => nenhum dado Google foi coletado. O diagnóstico
(`probe`) registra a resposta real do endpoint sem credenciais (403 PERMISSION_DENIED).

Pontos de conformidade (resumo; ver docs/google-module.md):
- Places API devolve no máximo 5 avaliações "mais relevantes" por lugar: NÃO é o histórico nem amostra
  representativa. `rating` e `userRatingCount` refletem o total do Google.
- Os campos rating/userRatingCount/reviews pertencem a SKUs pagos (Enterprise) => só rodam com
  `--authorize-billing` E GOOGLE_MAPS_API_KEY. Sem as duas coisas o código se recusa a chamar.
- Termos do Google: não copiar/armazenar conteúdo de avaliações além do permitido, manter atribuição,
  sem scraping do Maps. Por isso: texto de avaliação fica só em memória; persistimos apenas contagens por tema.
- Dados de avaliações de TODOS os clientes (histórico completo, respostas) exigem Business Profile API
  com autorização do proprietário (OAuth).
"""
from __future__ import annotations

import json
import os
import urllib.request

from .common import USER_AGENT, http_get_json, log_call, now_iso
from .extract import strip_accents

import re
import time

SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
ID_ONLY_MASK = "places.id,places.displayName,places.formattedAddress,places.location"  # Pro tier
REVIEW_MASK = "places.id,places.displayName,places.rating,places.userRatingCount,places.reviews"  # Enterprise

THEMES = {
    "comida": ["comida", "prato", "sabor", "saboros", "gostos", "delicios", "tempero", "cardapio", "porcao", "massa", "sushi", "carne"],
    "atendimento": ["atendimento", "atendid", "garcom", "garcon", "funcionari", "equipe", "gentil", "educad", "simpatic"],
    "tempo_espera": ["demor", "espera", "fila", "rapido", "rapidez", "esperamos", "tempo"],
    "preco_custo_beneficio": ["preco", "caro", "barato", "custo", "valor", "vale a pena", "cobram", "r$"],
    "ambiente": ["ambiente", "decoracao", "lugar", "limpo", "barulho", "aconchegante", "musica", "espaco", "vista"],
    "experiencia_geral": ["experiencia", "recomend", "voltaremos", "voltarei", "amei", "adorei", "pessim", "otim", "excelente", "ruim"],
}


def tag_themes(text: str) -> list[str]:
    low = strip_accents(text.lower())
    return [t for t, cues in THEMES.items() if any(re.search(r"(?<![a-z])" + re.escape(c), low) for c in cues)]


def probe() -> dict:
    """Diagnóstico sem credenciais (não faturável): prova verificável do estado de acesso."""
    body = json.dumps({"textQuery": "restaurante São Paulo"}).encode()
    req = urllib.request.Request(SEARCH_URL, data=body, method="POST", headers={
        "Content-Type": "application/json", "X-Goog-FieldMask": "places.id", "User-Agent": USER_AGENT})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            status, text = r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        status, text = e.code, e.read().decode("utf-8", "replace")
    log_call("google_places_probe", SEARCH_URL, status, time.time() - t0, "sem chave (diagnóstico)")
    try:
        err = json.loads(text).get("error", {})
    except Exception:
        err = {}
    return {"checked_at": now_iso(), "api_key_configured": bool(os.environ.get("GOOGLE_MAPS_API_KEY")),
            "http_status": status, "error_status": err.get("status"), "error_message": err.get("message"),
            "conclusion": "Places API (New) exige chave + faturamento habilitado no projeto Google Cloud; "
                          "sem isso, 403. Nenhum dado foi obtido nem simulado."}


def fetch_place(name: str, address: str, authorize_billing: bool = False) -> dict:
    """Busca UM lugar (Text Search, 1 chamada) pedindo rating/contagem/reviews. Recusa sem autorização."""
    key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not key:
        return {"status": "blocked_no_api_key"}
    if not authorize_billing:
        return {"status": "blocked_billing_not_authorized",
                "note": "campos rating/reviews são faturáveis; execute com --authorize-billing após aprovação do dono do projeto"}
    body = json.dumps({"textQuery": f"{name} {address}", "languageCode": "pt-BR", "maxResultCount": 1}).encode()
    req = urllib.request.Request(SEARCH_URL, data=body, method="POST", headers={
        "Content-Type": "application/json", "X-Goog-Api-Key": key, "X-Goog-FieldMask": REVIEW_MASK,
        "User-Agent": USER_AGENT})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=25) as r:
        data = json.loads(r.read().decode())
    log_call("google_places", SEARCH_URL, 200, time.time() - t0, "text_search+reviews (Enterprise SKU)")
    places = data.get("places", [])
    if not places:
        return {"status": "place_not_found"}
    p = places[0]
    reviews = p.get("reviews", [])
    theme_counts: dict = {}
    for rv in reviews:  # texto fica só em memória
        for t in tag_themes((rv.get("text") or {}).get("text", "")):
            theme_counts[t] = theme_counts.get(t, 0) + 1
    return {"status": "ok", "place_id": p.get("id"), "rating": p.get("rating"),
            "user_rating_count": p.get("userRatingCount"), "reviews_returned": len(reviews),
            "reviews_are_selected_not_sample": True, "theme_counts": theme_counts,
            "attribution": "Dados: Google Maps (exibir atribuição ao apresentar)"}


def maps_search_url(name: str, address: str) -> str:
    """URL oficial de busca do Google Maps (Maps URLs) apenas como referência humana de verificação.
    Nunca é requisitada/raspada por este projeto."""
    import urllib.parse
    return "https://www.google.com/maps/search/?api=1&query=" + urllib.parse.quote(f"{name} {address}")


def select_restaurants(restaurants: list[dict], n: int = 5) -> list[dict]:
    """Seleção determinística de até n restaurantes: capital de SP, coordenada exata, ordem por nº de
    publicações e rodízio entre influenciadores (para cobrir os três)."""
    pool = [r for r in restaurants if r.get("in_sao_paulo_city") and r.get("coordinate_quality") == "address_exact"]
    pool.sort(key=lambda r: (-len(r["post_ids"]), r["restaurant_id"]))
    chosen, seen = [], {}
    # 1ª passada: no máximo 2 por influenciador principal
    for r in pool:
        inf = r["influencers"][0]
        if seen.get(inf, 0) < 2 and len(chosen) < n:
            chosen.append(r)
            seen[inf] = seen.get(inf, 0) + 1
    return chosen

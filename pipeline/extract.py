"""Extração determinística (regras) de restaurante, endereço, recomendação e publicidade.

Entrada: texto público de uma publicação (hoje: título devolvido pelo índice de busca; ver
docs/access-investigation.md). Saída: campos estruturados + evidências curtas + confiança.

Princípios:
- Nunca inventar endereço: só copia o que está escrito no texto.
- Ausência de marcação de publicidade no texto disponível NÃO significa "sem publicidade":
  o campo `ad_disclosure` usa 'declared' ou 'not_detected_in_available_text'.
- Dúvida => review_status = 'pending_review'.
"""
from __future__ import annotations

import re
import unicodedata

AD_RE = re.compile(r"(\*\s*publi\b|#\s*publi\b|\bpubli\b|#ad\b|\bparceria\b|\bpubl\w*i\b)", re.I)
CREDIT_RE = re.compile(r"(🎥|📹|cia dele|com o|com a)\s*@([\w.]+)", re.I)
MENTION_RE = re.compile(r"@([A-Za-z0-9_.]{3,30})")
PIN_RE = re.compile(r"📍\s*([^📍#*\n]+)")
HASHTAG_RE = re.compile(r"#([\wÀ-ÿ]+)")
POSITIVE = [
    "amamos", "amei", "incrível", "incrivel", "melhor", "perfeit", "apaixonad", "maravilh",
    "excepcional", "recomend", "vale a pena", "surpreendeu", "delicios", "deliciosa",
    "não tem erro", "nao tem erro", "magnífico", "top 1", "favorit", "premiado", "raiz",
]
# hashtags genéricas que não são nomes de restaurante
GENERIC_TAGS = {
    "restaurante", "comeremsp", "reviewsporsp", "dicas", "dicassp", "restaurantesp", "restaurantessp",
    "hamburguer", "hamburgueria", "food", "comida", "sp", "saopaulo", "fyp", "rodizio", "pizza",
    "dicasderestaurantes", "restaurantepremiado", "primeiroencontro", "date", "casal", "bar",
    "sushi", "comidajaponesa", "rodiziojapones", "viral", "tiktok", "bares", "praia", "mar",
}
NON_SP_HINTS = {
    "atibaia": "Atibaia", "osasco": "Osasco", "guarulhos": "Guarulhos", "mairiporã": "Mairiporã",
    "santo andré": "Santo André", "pitangueiras": "Guarujá", "bangkok": "Bangkok", "paris": "Paris",
}


def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def normalize_address(addr: str) -> str:
    """Chave de deduplicação: logradouro + número, sem acento/pontuação/abreviação comum."""
    a = strip_accents(addr).lower()
    a = re.sub(r"\b(rua|r\.|av\.?|avenida|al\.?|alameda|pca\.?|praca|estrada|est\.?)\b", lambda m: {
        "rua": "r", "r.": "r", "av": "av", "av.": "av", "avenida": "av", "al": "al", "al.": "al",
        "alameda": "al", "pca": "pc", "pca.": "pc", "praca": "pc", "estrada": "estr", "est": "estr",
        "est.": "estr"}.get(m.group(0), m.group(0)), a)
    a = re.sub(r"[^a-z0-9 ]", " ", a)
    m = re.match(r"\s*(?:(\w+)\s+)?(.*?)\s+(\d{1,5})\b", a)
    if not m:
        return re.sub(r"\s+", " ", a).strip()
    street = re.sub(r"\s+", " ", f"{m.group(1) or ''} {m.group(2)}").strip()
    return f"{street} {m.group(3)}"


def humanize_handle(h: str) -> str:
    h = re.sub(r"(oficial|sp|restaurante|ristorante|bar)$", lambda m: " " + m.group(0), h, flags=re.I) if False else h
    return h.replace("_", " ").replace(".", " ").strip().title()


def detect_ad(text: str) -> str:
    return "declared" if AD_RE.search(text) else "not_detected_in_available_text"


VISIT = ["conhecemos", "fomos", "voltamos", "viemos", "conheci", "provei", "pedimos", "pegamos"]


def detect_recommendation(text: str, has_venue: bool) -> str:
    """recommendation = avaliação positiva explícita; visit_showcase = visita/cardápio sem
    avaliação explícita no texto disponível; mention_only = só citação; unknown = sem restaurante."""
    low = strip_accents(text.lower())
    pos = any(strip_accents(p) in low for p in POSITIVE)
    visit = any(v in low for v in VISIT)
    if not has_venue:
        return "unknown"
    if pos:
        return "recommendation"
    if visit:
        return "visit_showcase"
    return "mention_only"


def pick_venue_handles(text: str) -> list[str]:
    credits = {m.group(2).lower() for m in CREDIT_RE.finditer(text)}
    counts: dict[str, int] = {}
    order: list[str] = []
    for m in MENTION_RE.finditer(text):
        h = m.group(1).lower().rstrip(".")
        if h in credits:
            continue
        if h not in counts:
            order.append(h)
        counts[h] = counts.get(h, 0) + 1
    return sorted(order, key=lambda h: (-counts[h], order.index(h)))


EMOJI_RE = re.compile("[\U0001F000-\U0001FFFF\u2600-\u27BF\u203C\uFE0F]")
ADDR_CUT = [" Fomos ", " Do lado", " Aceitam", "(", " Eles ", " Pedimos", " Lugar "]
LABEL_RE = re.compile(r"^[A-ZÀ-Ý][A-ZÀ-Ý ]{2,19}\s+-\s+(?=\S)")  # 'CARRÃO - Av. ...' (rótulo da unidade)
STREET_RE = re.compile(
    r"((?:R\.|Rua|Av\.?|Avenida|Al\.|Alameda|Estrada|Praça)\s+[^,#\n]{3,60}?,?\s*\d{1,5}[^#\n📍]{0,45})")


def clean_address(raw: str) -> str:
    raw = EMOJI_RE.split(raw)[0]
    for cut in ADDR_CUT:
        raw = raw.split(cut)[0]
    raw = re.sub(r"^(Local|Rua):\s*", lambda m: "Rua " if m.group(1) == "Rua" else "", raw)
    return re.sub(r"\s+", " ", raw).strip(" -–—.,")


def extract_units(text: str) -> list[dict]:
    """Retorna as unidades (endereços) citadas via 📍; sem 📍, tenta um endereço de rua no texto."""
    units = []
    for m in PIN_RE.finditer(text):
        raw = clean_address(m.group(1))
        if not re.search(r"\d", raw) and "sem número" not in raw.lower():
            # 📍 sem número (ex.: "Praia de Pitangueiras", "Local: ...") ainda é evidência de local
            units.append({"raw": raw, "has_number": False})
        else:
            units.append({"raw": raw, "has_number": True})
    if not units:
        m = STREET_RE.search(text)
        if m:
            units.append({"raw": clean_address(m.group(1)), "has_number": True, "fallback": True})
    return units


def split_name_address(raw: str):
    """'Legado Parrilla - R. Mal. Barbacena, 555 - Vila Reg. Feijó, São Paulo' -> (nome, endereço)."""
    m = re.match(r"^([^,\d]{3,60}?)\s+-\s+((?:R\.|Rua|Av\.|Avenida|Al\.|Alameda)(?=\s).*)$", raw)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return None, raw


def detect_municipality(text: str) -> str | None:
    low = text.lower()
    for k, v in NON_SP_HINTS.items():
        if k in low:
            return v
    return None


def extract(text: str) -> dict:
    """Extrai campos de um texto de publicação. Determinístico e testável."""
    handles = pick_venue_handles(text)
    units = extract_units(text)
    evidence: list[str] = []
    name = None
    name_source = None
    address = None
    extra_units = []

    if units:
        n, addr = split_name_address(units[0]["raw"])
        if n and not handles:
            name, name_source = n, "pin_prefix"
            evidence.append(f"📍 {units[0]['raw'][:110]}")
        address = addr
        extra_units = [u["raw"] for u in units[1:]]
        if not (n and not handles):
            evidence.append(f"📍 {units[0]['raw'][:110]}")
            address = units[0]["raw"]
    if handles:
        evidence.append("@" + handles[0])
        if not name:
            name, name_source = humanize_handle(handles[0]), "mention_handle"
    tag_candidates = [t for t in HASHTAG_RE.findall(text) if t.lower() not in GENERIC_TAGS]

    has_venue = bool(name)
    rec = detect_recommendation(text, has_venue)
    ad = detect_ad(text)
    if ad == "declared":
        evidence.append("marcação de publicidade no texto")

    if name_source in ("mention_handle", "pin_prefix") and address and any(c.isdigit() for c in address):
        conf = "high"
    elif name_source in ("mention_handle", "pin_prefix") or (address and name):
        conf = "medium"
    elif name:
        conf = "low"
    else:
        conf = "none"

    return {
        "venue_handle": handles[0] if handles else None,
        "venue_handles_all": handles,
        "hashtag_candidates": tag_candidates[:6],  # NÃO são nomes confirmados (podem ser pratos/temas)
        "venue_name": name,
        "name_source": name_source,
        "address_text": address,
        "extra_unit_addresses": extra_units,
        "municipality_hint": detect_municipality(text),
        "recommendation_type": rec,
        "ad_disclosure": ad,
        "evidence": evidence,
        "confidence": conf,
        "review_status": "auto_ok" if conf == "high" else ("pending_review"),
    }

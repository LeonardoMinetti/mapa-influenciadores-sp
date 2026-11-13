"""Geocodificação via Nominatim (OpenStreetMap) — fonte cujo uso é permitido (ODbL, atribuição
"© colaboradores do OpenStreetMap"). Política de uso respeitada: 1 req/s, User-Agent identificado,
cache em disco, sem lote massivo. Para produção comercial, usar instância própria ou provedor pago.

Dois passos por restaurante:
 1. endereço -> coordenadas (match_type = 'address')
 2. nome do estabelecimento dentro de uma caixa pequena ao redor do endereço
    (existência em OSM; match_type = 'poi' se encontrado). Sem POI => existência NÃO verificada.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
import urllib.parse

from .common import RAW, http_get_json, now_iso
from .extract import strip_accents

NOMINATIM = "https://nominatim.openstreetmap.org/search"
_last_call = [0.0]


def _cache_path(key: str):
    d = RAW / "nominatim"
    d.mkdir(parents=True, exist_ok=True)
    return d / (hashlib.sha1(key.encode()).hexdigest()[:16] + ".json")


def _search(params: dict) -> list:
    qs = urllib.parse.urlencode({"format": "jsonv2", "addressdetails": 1, "limit": 3,
                                 "countrycodes": "br", "accept-language": "pt-BR", **params})
    url = f"{NOMINATIM}?{qs}"
    cp = _cache_path(url)
    if cp.exists():
        return json.loads(cp.read_text(encoding="utf-8"))["results"]
    wait = 1.1 - (time.time() - _last_call[0])
    if wait > 0:
        time.sleep(wait)
    status, body = http_get_json("nominatim", url)
    _last_call[0] = time.time()
    results = body if isinstance(body, list) else []
    cp.write_text(json.dumps({"fetched_at": now_iso(), "status": status, "url": url, "results": results},
                             ensure_ascii=False, indent=1), encoding="utf-8")
    return results


def _tokens(name: str) -> set:
    import re
    from .extract import strip_accents
    return {t for t in re.findall(r"[a-z0-9]{3,}", strip_accents(name).lower())
            if t not in {"restaurante", "bar", "sushi", "pizzaria", "sp"}}


ABBREV = {r"\bR\.": "Rua", r"\bAv\.": "Avenida", r"\bAl\.": "Alameda", r"\bGen\.": "General",
          r"\bProf\.?(?=\s)": "Professor", r"\bMal\.": "Marechal", r"\bEng\.": "Engenheiro",
          r"\bVer\.": "Vereador", r"\bDr\.": "Doutor", r"\bCel\.": "Coronel", r"\bPres\.": "Presidente"}


def simplify_address(address: str, city: str) -> str:
    """Segunda tentativa: expande abreviações e descarta bairro/complemento após o número."""
    import re
    a = address
    for pat, rep in ABBREV.items():
        a = re.sub(pat, rep, a)
    m = re.match(r"(.*?\d{1,5})\b", a)
    if m:
        a = m.group(1)
    a = a.replace(" - ", " ")
    return f"{a}, {city}"


def geocode_restaurant(name: str, address: str, municipality: str | None) -> dict:
    city = municipality or "São Paulo"
    q = f"{address}, {city}" if city.lower() not in address.lower() else address
    res = _search({"q": q})
    if not res:
        q2 = simplify_address(address, city)
        res = _search({"q": q2})
        if res:
            q = q2
    out = {"query": q, "status": "not_found", "lat": None, "lon": None, "osm": None,
           "match_type": None, "display_name": None, "neighborhood": None, "municipality": None,
           "poi_found": False, "poi_name": None, "source": "OpenStreetMap Nominatim (ODbL)"}
    if not res:
        return out

    def muni_of(r):
        a = r.get("address", {})
        return a.get("city") or a.get("town") or a.get("municipality") or a.get("village")

    expected = (municipality or "São Paulo")
    ok = [r for r in res if strip_accents(muni_of(r) or "").lower() == strip_accents(expected).lower()]
    if not ok:  # rua existe em outro município: NÃO aceitar (ex.: homônimas)
        out.update({"status": "municipality_mismatch", "rejected_candidate": res[0].get("display_name"),
                    "municipality": muni_of(res[0])})
        return out
    top = ok[0]
    ad = top.get("address", {})
    cat = f"{top.get('category')}/{top.get('type')}"
    if ad.get("house_number") or top.get("category") == "place" and top.get("type") == "house":
        quality = "address_exact"
    elif cat.startswith(("leisure/", "natural/", "boundary/", "place/")):
        quality = "area"
    else:
        quality = "street_approx"
    if quality == "address_exact" and "sem número" in address.lower():
        quality = "street_approx"  # endereço sem número nunca é "exato"
    # coerência com o bairro escrito no texto da publicação (após o último ' - ')
    hint = address.rsplit(" - ", 1)[-1] if " - " in address else ""
    consistent = None
    if hint and not re.search(r"\d", hint):
        h = {t for t in _tokens(hint) if t not in {"sao", "paulo", "jardim", "vila", "parque"}}
        disp = strip_accents(top.get("display_name", "")).lower()
        consistent = (not h) or any(t in disp for t in h)
    out.update({
        "status": "found", "lat": float(top["lat"]), "lon": float(top["lon"]),
        "osm": f"{top.get('osm_type')}/{top.get('osm_id')}", "match_type": "address",
        "osm_category": cat, "house_level": quality == "address_exact", "coordinate_quality": quality,
        "neighborhood_consistent": consistent,
        "display_name": top.get("display_name"),
        "neighborhood": ad.get("suburb") or ad.get("neighbourhood") or ad.get("quarter"),
        "municipality": muni_of(top),
    })
    # passo 2: POI por nome perto do endereço (caixa ~±1,2 km)
    d = 0.011
    vb = f"{out['lon'] - d},{out['lat'] + d},{out['lon'] + d},{out['lat'] - d}"
    pois = _search({"q": name, "viewbox": vb, "bounded": 1})
    want = _tokens(name)
    for p in pois:
        got = _tokens(p.get("name") or p.get("display_name", "").split(",")[0])
        if want and got and (want & got):
            out.update({"poi_found": True, "poi_name": p.get("name"),
                        "poi_osm": f"{p.get('osm_type')}/{p.get('osm_id')}",
                        "poi_lat": float(p["lat"]), "poi_lon": float(p["lon"])})
            break
    return out

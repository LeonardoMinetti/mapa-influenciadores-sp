"""Fotos dos restaurantes — SÓ fontes com licença ou autorização registrada.

Fontes tratadas (nenhuma cópia de Google/Instagram/sites de terceiros):
 1. `add_manual()` — foto fornecida pelo restaurante ou pelo criador, com autorização (crédito + licença no manifesto).
 2. `fetch_mapillary()` — fachada via Mapillary (imagens colaborativas CC BY-SA 4.0), exige MAPILLARY_ACCESS_TOKEN
    (gratuito). ESTADO: código escrito mas NÃO testado contra a API (sem token nesta PoC); a escolha geométrica da
    imagem tem testes. As URLs do Mapillary expiram, então a imagem é baixada e versionada com atribuição.
 3. Google Places Photos — só com chave/faturamento e sem armazenar (ver docs/google-module.md). Não implementado.

Testado nesta PoC: Wikimedia Commons (busca por nome do restaurante) => nenhuma foto utilizável.
Manifesto: data/public/photos.json  {restaurant_id: {file, credit, license, source_url, fetched_on}}
"""
from __future__ import annotations

import json
import math
import os
import shutil
import urllib.parse
import urllib.request
from pathlib import Path

from .common import PUBLIC, USER_AGENT, http_get_json, now_iso

PHOTOS_DIR = PUBLIC / "photos"
MANIFEST = PUBLIC / "photos.json"


def load_manifest() -> dict:
    try:
        return json.loads(MANIFEST.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_manifest(m: dict) -> None:
    MANIFEST.write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")


def add_manual(restaurant_id: str, src: str, credit: str, license: str, source_url: str = "") -> dict:
    """Registra uma foto fornecida com autorização. `license` ex.: 'autorização do restaurante (2026-11-20)'."""
    if not credit or not license:
        raise ValueError("crédito e licença/autorização são obrigatórios")
    PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
    ext = Path(src).suffix.lower() or ".jpg"
    dest = PHOTOS_DIR / f"{restaurant_id}{ext}"
    shutil.copyfile(src, dest)
    m = load_manifest()
    m[restaurant_id] = {"file": f"photos/{dest.name}", "credit": credit, "license": license,
                        "source_url": source_url, "fetched_on": now_iso()}
    save_manifest(m)
    return m[restaurant_id]


# ---- Mapillary -------------------------------------------------------------------------------

def bearing(lat1, lon1, lat2, lon2) -> float:
    """Azimute (graus, 0=norte) de (lat1,lon1) para (lat2,lon2)."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    y = math.sin(dl) * math.cos(p2)
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return (math.degrees(math.atan2(y, x)) + 360) % 360


def distance_m(lat1, lon1, lat2, lon2) -> float:
    R = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def angle_diff(a, b) -> float:
    d = abs(a - b) % 360
    return min(d, 360 - d)


def pick_best(candidates: list[dict], lat: float, lon: float, max_m: float = 45, max_angle: float = 40):
    """Escolhe a imagem mais próxima cuja câmera aponta para o ponto (fachada), preferindo a mais recente."""
    best, best_key = None, None
    for c in candidates:
        geo = (c.get("computed_geometry") or {}).get("coordinates")
        ang = c.get("computed_compass_angle")
        if not geo or ang is None:
            continue
        clon, clat = geo
        d = distance_m(clat, clon, lat, lon)
        if d > max_m or d < 3:
            continue
        if angle_diff(ang, bearing(clat, clon, lat, lon)) > max_angle:
            continue
        key = (round(d / 5), -(c.get("captured_at") or 0))
        if best_key is None or key < best_key:
            best, best_key = c, key
    return best


def fetch_mapillary(restaurants: list[dict], token: str | None = None) -> dict:
    """Baixa 1 fachada por restaurante de endereço exato. NÃO TESTADO contra a API real."""
    token = token or os.environ.get("MAPILLARY_ACCESS_TOKEN")
    if not token:
        return {"status": "blocked_no_token"}
    PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
    m = load_manifest()
    got = 0
    for r in restaurants:
        if r.get("coordinate_quality") != "address_exact" or r["restaurant_id"] in m:
            continue
        d = 0.0004  # ~45 m
        bbox = f"{r['lon'] - d},{r['lat'] - d},{r['lon'] + d},{r['lat'] + d}"
        qs = urllib.parse.urlencode({"access_token": token, "bbox": bbox, "limit": 60,
                                     "fields": "id,thumb_1024_url,computed_compass_angle,computed_geometry,captured_at,creator"})
        status, body = http_get_json("mapillary", f"https://graph.mapillary.com/images?{qs}")
        if status != 200 or not body:
            continue
        best = pick_best(body.get("data", []), r["lat"], r["lon"])
        if not best or not best.get("thumb_1024_url"):
            continue
        dest = PHOTOS_DIR / f"{r['restaurant_id']}.jpg"
        req = urllib.request.Request(best["thumb_1024_url"], headers={"User-Agent": USER_AGENT})
        dest.write_bytes(urllib.request.urlopen(req, timeout=30).read())
        who = (best.get("creator") or {}).get("username", "colaborador Mapillary")
        m[r["restaurant_id"]] = {"file": f"photos/{dest.name}", "credit": f"Mapillary · {who}", "license": "CC BY-SA 4.0",
                                 "source_url": f"https://www.mapillary.com/app/?pKey={best['id']}", "fetched_on": now_iso()}
        got += 1
    save_manifest(m)
    return {"status": "ok", "photos_added": got}

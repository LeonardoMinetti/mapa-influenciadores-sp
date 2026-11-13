"""Coletor TikTok via oEmbed oficial (https://www.tiktok.com/oembed).

Método permitido: endpoint público e documentado do TikTok, consultado URL a URL.
NÃO faz scraping de páginas de perfil (robots.txt do TikTok proíbe), NÃO usa login,
NÃO contorna bloqueios. A *descoberta* das URLs vem de data/seeds/tiktok_urls.csv
(índice de busca web ou lista fornecida pelo usuário).

Limitações registradas: oEmbed não devolve data, contagem de curtidas nem comentários.
A data é derivada do ID do vídeo (ID de 64 bits; os 32 bits altos são um timestamp Unix).
"""
from __future__ import annotations

import csv
import json
import time
import urllib.parse
from datetime import datetime, timezone

from .common import RAW, SEEDS, http_get_json, now_iso

OEMBED = "https://www.tiktok.com/oembed?url="


def date_from_video_id(video_id: str) -> str:
    ts = int(video_id) >> 32
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")


def read_seeds() -> list[dict]:
    with open(SEEDS / "tiktok_urls.csv", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def collect(sleep: float = 0.6, force: bool = False) -> list[dict]:
    out_dir = RAW / "tiktok_oembed"
    out_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for seed in read_seeds():
        vid, handle, url = seed["post_id"], seed["handle"], seed["url"]
        cache = out_dir / f"{vid}.json"
        if cache.exists() and not force:
            rec = json.loads(cache.read_text(encoding="utf-8"))
            results.append(rec)
            continue
        status, body = http_get_json("tiktok_oembed", OEMBED + urllib.parse.quote(url, safe=""))
        rec = {
            "seed": seed,
            "fetched_at": now_iso(),
            "http_status": status,
            "ok": status == 200 and isinstance(body, dict) and "title" in body,
            "response": body,
        }
        if rec["ok"]:
            author = (body.get("author_unique_id") or body.get("author_url", "").rsplit("@", 1)[-1]).lower()
            rec["author_matches_expected"] = author == handle.lower()
        cache.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
        results.append(rec)
        time.sleep(sleep)
    return results


def collect_profiles() -> dict:
    """Confirma a existência/identidade dos perfis via oEmbed oficial de criador (funciona só para perfil)."""
    out = {}
    for h in ("reviewsporsp", "incrivelsp", "vivamaissp"):
        url = f"https://www.tiktok.com/@{h}"
        status, body = http_get_json("tiktok_oembed_profile", OEMBED + urllib.parse.quote(url, safe=""))
        out[h] = {"checked_at": now_iso(), "http_status": status, "url": url,
                  "author_name": (body or {}).get("author_name"), "title": (body or {}).get("title"),
                  "confirmed": status == 200 and bool(body and body.get("author_url", "").lower().endswith("@" + h))}
        time.sleep(0.5)
    (RAW / "tiktok_profiles.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


if __name__ == "__main__":
    print(json.dumps(collect_profiles(), ensure_ascii=False, indent=1))
    res = collect()
    ok = sum(r["ok"] for r in res)
    print(f"tentadas={len(res)} recuperadas={ok}")

"""Une sementes + texto público + extração + anotações -> publicações, restaurantes e relações.

Regras de consolidação:
- restaurante = (nome-base, endereço normalizado). Dois @ diferentes com o mesmo endereço
  (ex.: pizzariamammaconcetta / pizzeriamammaconcetta) são o MESMO restaurante.
- unidades diferentes da mesma rede (endereços diferentes) viram restaurantes distintos,
  agrupados por `brand_key`.
- publicações sem restaurante identificável ficam registradas, sem restaurante, em revisão.
"""
from __future__ import annotations

import csv
import json
import re

from .collect_tiktok import date_from_video_id
from .common import INFLUENCERS, PRIVATE, SEEDS
from .extract import LABEL_RE, detect_municipality, extract, normalize_address, strip_accents

MUNI_BY_ADDRESS = {"alphaville": "Barueri", "osasco": "Osasco", "guarulhos": "Guarulhos",
                   "santo andré": "Santo André", "atibaia": "Atibaia", "mairiporã": "Mairiporã"}


def brand_key(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", strip_accents(name).lower())


def load_inputs():
    with open(SEEDS / "tiktok_urls.csv", encoding="utf-8") as f:
        seeds = list(csv.DictReader(f))
    snippets = json.load(open(PRIVATE / "search_snippets.json", encoding="utf-8"))["items"]
    annotations = json.load(open(SEEDS / "annotations.json", encoding="utf-8"))
    return seeds, snippets, annotations


def unit_municipality(addr: str):
    low = addr.lower()
    for k, v in MUNI_BY_ADDRESS.items():
        if k in low:
            return v
    return None


def consolidate(seeds, snippets, annotations):
    names = annotations["display_names_by_handle"]
    posts, restaurants, links = [], {}, []
    for s in seeds:
        pid = s["post_id"]
        snip = snippets.get(pid, {})
        text = snip.get("snippet", "")
        e = extract(text)
        ov = annotations.get("post_overrides", {}).get(pid, {})
        name = e["venue_name"]
        name_source = e["name_source"]
        if e["venue_handle"] and e["venue_handle"] in names:
            name, name_source = names[e["venue_handle"]], "annotator_from_handle"
        if ov.get("venue_name"):
            name, name_source = ov["venue_name"], ov.get("name_source", "annotator")
        if name and e["confidence"] == "none":
            e["confidence"] = "medium"
        trimmed = bool(snip.get("trimmed"))
        notes = [n for n in (annotations.get("post_notes", {}).get(pid), ov.get("note")) if n]
        limitations = ["Conteúdo do vídeo não processado (só texto público disponível)."]
        if trimmed:
            limitations.append("Texto reduzido pelo índice de busca; avaliação/publicidade podem estar na parte omitida.")
        post = {
            "post_id": pid, "platform": "tiktok", "influencer": s["handle"], "url": s["url"],
            "posted_on": date_from_video_id(pid), "date_source": "derived_from_video_id",
            "text_source": "web_search_index_title", "text_trimmed": trimmed,
            "recommendation_type": e["recommendation_type"] if name else "unknown",
            "ad_disclosure": e["ad_disclosure"], "evidence": e["evidence"],
            "hashtag_candidates": e["hashtag_candidates"], "confidence": e["confidence"] if name else "none",
            "limitations": limitations, "notes": notes, "restaurant_ids": [],
            "review_status": "auto_ok" if (name and e["confidence"] == "high") else "pending_review",
        }
        if name:
            addrs = []
            if e["address_text"]:
                addrs.append(e["address_text"])
            for x in e["extra_unit_addresses"]:
                if normalize_address(x) not in {normalize_address(a) for a in addrs}:
                    addrs.append(x)
            if not addrs:
                addrs = [None]
            for addr_raw in addrs:
                addr, unit_label = addr_raw, None
                if addr_raw:
                    m = LABEL_RE.match(addr_raw)
                    if m:
                        unit_label = m.group(0).rsplit("-", 1)[0].strip().title()
                        addr = LABEL_RE.sub("", addr_raw)
                key = (brand_key(name), normalize_address(addr) if addr else "")
                rid = "r_" + brand_key(name)[:24] + ("_" + re.sub(r"\W", "", normalize_address(addr))[:14] if addr else "")
                if key not in restaurants:
                    muni = (unit_municipality((unit_label or "") + " " + (addr or "")) if addr else None) or (detect_municipality(addr or "") or None)
                    restaurants[key] = {
                        "restaurant_id": rid, "brand_key": brand_key(name), "name": name, "name_source": name_source,
                        "address_text": addr, "unit_label": unit_label, "municipality_hint": muni,
                        "multi_unit_brand": False, "post_ids": [], "influencers": [],
                    }
                r = restaurants[key]
                r["post_ids"].append(pid)
                if s["handle"] not in r["influencers"]:
                    r["influencers"].append(s["handle"])
                post["restaurant_ids"].append(r["restaurant_id"])
                links.append({"post_id": pid, "restaurant_id": r["restaurant_id"],
                              "relation": e["recommendation_type"]})
        posts.append(post)
    rlist = list(restaurants.values())
    by_brand = {}
    for r in rlist:
        by_brand.setdefault(r["brand_key"], []).append(r)
    for brand, rs in by_brand.items():
        if len(rs) > 1:
            for r in rs:
                r["multi_unit_brand"] = True
    return posts, rlist, links

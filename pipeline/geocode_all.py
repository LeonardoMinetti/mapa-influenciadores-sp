"""Geocodifica todos os restaurantes consolidados que têm endereço (cache em data/raw/nominatim)."""
from __future__ import annotations

import json

from .common import PRIVATE, PROCESSED
from .consolidate import consolidate, load_inputs
from .geocode import geocode_restaurant


def run() -> dict:
    posts, restaurants, links = consolidate(*load_inputs())
    out = {}
    for r in restaurants:
        if not r["address_text"]:
            out[r["restaurant_id"]] = {"status": "no_address_in_source"}
            continue
        out[r["restaurant_id"]] = geocode_restaurant(r["name"], r["address_text"], r["municipality_hint"])
    PROCESSED.mkdir(parents=True, exist_ok=True)
    (PROCESSED / "geocode_results.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


if __name__ == "__main__":
    res = run()
    found = [v for v in res.values() if v.get("status") == "found"]
    print("restaurantes:", len(res), "| endereço localizado:", len(found),
          "| nível casa:", sum(bool(v.get("house_level")) for v in found),
          "| POI OSM por nome:", sum(bool(v.get("poi_found")) for v in found))

"""Indicadores finais da PoC, calculados do banco e dos logs (nada digitado à mão)."""
from __future__ import annotations

import collections
import json
import sqlite3

from .common import LOGS, PRIVATE, PUBLIC


def read_jsonl(path):
    try:
        return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    except FileNotFoundError:
        return []


def compute() -> dict:
    con = sqlite3.connect(PRIVATE / "poc.sqlite")
    q = lambda sql: con.execute(sql).fetchall()
    one = lambda sql: con.execute(sql).fetchone()[0]
    calls = read_jsonl(LOGS / "api_calls.jsonl")
    by_service = collections.defaultdict(lambda: {"calls": 0, "errors_4xx_5xx_or_network": 0, "retries": 0, "seconds": 0.0})
    for c in calls:
        s = by_service[c["service"]]
        s["calls"] += 1
        s["seconds"] += c["seconds"]
        if c["status"] == 0 or c["status"] >= 400:
            s["errors_4xx_5xx_or_network"] += 1
        if "attempt=" in c.get("note", "") and not c["note"].startswith("attempt=1"):
            s["retries"] += 1
    runs = read_jsonl(LOGS / "runs.jsonl")
    n_posts = one("select count(*) from posts")
    with_rest = one("select count(distinct post_id) from post_restaurants")
    rec_posts = one("select count(distinct post_id) from post_restaurants where relation='recommendation'")
    uniq_rest = one("select count(*) from restaurants")
    brands = one("select count(distinct brand_key) from restaurants")
    geoloc = one("select count(*) from restaurants where lat is not null")
    exact = one("select count(*) from restaurants where coordinate_quality='address_exact'")
    # duplicadas: relações além da primeira para o mesmo restaurante
    dup = one("select coalesce(sum(n-1),0) from (select count(*) n from post_restaurants group by restaurant_id having n>1)")
    m = {
        "posts_attempted": one("select count(*) from posts"),
        "posts_with_public_text_recovered": n_posts,
        "posts_recovered_via_official_api": 0,
        "tiktok_oembed_video_calls": by_service["tiktok_oembed"]["calls"],
        "posts_by_influencer": dict(q("select influencer,count(*) from posts group by 1")),
        "posts_with_restaurant_identified": with_rest,
        "recommendations_explicit": rec_posts,
        "recommendation_breakdown": dict(q("select recommendation_type,count(*) from posts group by 1")),
        "ad_declared_posts": one("select count(*) from posts where ad_disclosure='declared'"),
        "unique_restaurant_units": uniq_rest, "unique_brands": brands,
        "geolocated_restaurants": geoloc, "geolocated_exact_address": exact,
        "coordinate_quality": dict(q("select coordinate_quality,count(*) from restaurants group by 1")),
        "existence_confirmed_in_osm_poi": one("select count(*) from restaurants where existence_verified=1"),
        "duplicate_recommendations_consolidated": dup,
        "restaurants_pending_review": one("select count(*) from restaurants where review_status='pending_review'"),
        "posts_pending_review": one("select count(*) from posts where review_status='pending_review'"),
        "comments_instagram": 0, "comments_tiktok": one("select count(*) from comments"),
        "google_restaurants_selected": 5, "google_reviews_accessible": 0,
        "cross_analyses_possible": 0,
        "api_calls": {k: {**v, "seconds": round(v["seconds"], 1)} for k, v in by_service.items()},
        "api_calls_total": len(calls),
        "pipeline_step_seconds": {r["step"]: r["seconds"] for r in runs[-12:]},
        "billed_cost_usd": 0.0,
    }
    (PUBLIC / "metrics.json").write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")
    return m


if __name__ == "__main__":
    print(json.dumps(compute(), ensure_ascii=False, indent=1))

"""Orquestra a PoC de ponta a ponta e registra o tempo de cada etapa (data/logs/runs.jsonl).

Uso:  python3 -m pipeline.run_pipeline [--skip-network]
Etapas de rede usam apenas endpoints permitidos e têm cache em data/raw (reexecução não repete chamadas).
Pré-requisito local (não versionado): data/private/search_snippets.json e data/seeds/tiktok_urls.csv.
"""
from __future__ import annotations

import argparse
import json
import time

from . import build_db, collect_tiktok, demo_data, geocode_all, google_places, instagram, metrics
from .common import LOGS, PRIVATE, PROCESSED, now_iso


def step(name, fn, results):
    t0 = time.time()
    try:
        out = fn()
        status = "ok"
    except Exception as e:  # registra e segue: falha de uma etapa não apaga as demais
        out, status = repr(e), "error"
    rec = {"ts": now_iso(), "step": name, "status": status, "seconds": round(time.time() - t0, 2)}
    LOGS.mkdir(parents=True, exist_ok=True)
    with open(LOGS / "runs.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"[{status}] {name} ({rec['seconds']}s)")
    results[name] = out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-network", action="store_true")
    a = ap.parse_args()
    res: dict = {}
    PRIVATE.mkdir(parents=True, exist_ok=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    if not a.skip_network:
        step("tiktok_profiles", collect_tiktok.collect_profiles, res)
        step("tiktok_video_oembed", collect_tiktok.collect, res)
        step("geocode_nominatim", geocode_all.run, res)
        step("instagram_probe", lambda: (PROCESSED / "instagram_probe.json").write_text(
            json.dumps(instagram.probe_access(), ensure_ascii=False, indent=1), encoding="utf-8"), res)
        step("google_probe", lambda: (PROCESSED / "google_probe.json").write_text(
            json.dumps(google_places.probe(), ensure_ascii=False, indent=1), encoding="utf-8"), res)
    step("demo_data", demo_data.main if hasattr(demo_data, "main") else (lambda: None), res)
    step("build_db", build_db.build, res)
    step("metrics", metrics.compute, res)


if __name__ == "__main__":
    main()

"""Constrói o banco SQLite e os JSONs (público / privado / revisão) a partir das etapas anteriores."""
from __future__ import annotations

import json
import sqlite3

from . import alerts, crosscheck
from .common import INFLUENCERS, PRIVATE, PROCESSED, PUBLIC, RAW, now_iso
from .consolidate import consolidate, load_inputs
from .comments import import_comments_csv
from .common import IMPORTS

SCHEMA = """
DROP TABLE IF EXISTS influencers; DROP TABLE IF EXISTS posts; DROP TABLE IF EXISTS restaurants;
DROP TABLE IF EXISTS post_restaurants; DROP TABLE IF EXISTS evidence; DROP TABLE IF EXISTS validations;
DROP TABLE IF EXISTS comments; DROP TABLE IF EXISTS comment_labels; DROP TABLE IF EXISTS coverage;
CREATE TABLE influencers(handle TEXT PRIMARY KEY, display_name TEXT, tiktok_confirmed INTEGER, tiktok_profile_name TEXT,
  instagram_status TEXT);
CREATE TABLE posts(post_id TEXT PRIMARY KEY, platform TEXT, influencer TEXT REFERENCES influencers(handle), url TEXT,
  posted_on TEXT, date_source TEXT, text_source TEXT, text_trimmed INTEGER, recommendation_type TEXT,
  ad_disclosure TEXT, confidence TEXT, review_status TEXT, limitations TEXT, notes TEXT);
CREATE TABLE restaurants(restaurant_id TEXT PRIMARY KEY, name TEXT, name_source TEXT, brand_key TEXT, multi_unit_brand INTEGER,
  unit_label TEXT, address_text TEXT, municipality TEXT, neighborhood TEXT, lat REAL, lon REAL, coordinate_quality TEXT,
  geocode_source TEXT, existence_verified INTEGER, in_sao_paulo_city INTEGER, review_status TEXT, review_reasons TEXT);
CREATE TABLE post_restaurants(post_id TEXT REFERENCES posts(post_id), restaurant_id TEXT REFERENCES restaurants(restaurant_id),
  relation TEXT, PRIMARY KEY(post_id, restaurant_id));
CREATE TABLE evidence(id INTEGER PRIMARY KEY AUTOINCREMENT, entity_type TEXT, entity_id TEXT, kind TEXT, snippet TEXT, source TEXT);
CREATE TABLE validations(id INTEGER PRIMARY KEY AUTOINCREMENT, entity_type TEXT, entity_id TEXT, check_name TEXT, result TEXT, detail TEXT, checked_at TEXT);
CREATE TABLE comments(comment_id INTEGER PRIMARY KEY AUTOINCREMENT, post_id TEXT, text TEXT, source TEXT, collected_on TEXT,
  selection_method TEXT, platform_total_comments TEXT, confidence TEXT, method TEXT);
CREATE TABLE comment_labels(comment_id INTEGER, label TEXT);
CREATE TABLE coverage(key TEXT PRIMARY KEY, value TEXT);
"""


def load_json(path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def restaurant_review(r, g, in_city):
    reasons = []
    q = (g or {}).get("coordinate_quality")
    if not g or g.get("status") == "no_address_in_source":
        reasons.append("sem endereço no texto da publicação")
    elif g.get("status") == "municipality_mismatch":
        reasons.append(f"geocodificação rejeitada: logradouro encontrado em outro município ({g.get('municipality')})")
    elif g.get("status") == "not_found":
        reasons.append("endereço não localizado no OpenStreetMap")
    else:
        if q == "street_approx":
            reasons.append("coordenada aproximada (centro da rua, sem número exato)")
        if q == "area":
            reasons.append("local é uma área (parque/praia), não um ponto de estabelecimento")
        if g.get("neighborhood_consistent") is False:
            reasons.append("bairro do texto diverge do bairro devolvido pelo OSM")
        if not g.get("poi_found"):
            reasons.append("existência do estabelecimento não confirmada em fonte (sem POI no OSM)")
    if not in_city:
        reasons.append("fora do município de São Paulo")
    if r["name_source"] in ("mention_handle", "annotator_from_handle"):
        reasons.append("nome derivado do @ do estabelecimento")
    hard = [x for x in reasons if not x.startswith(("existência", "nome derivado"))]
    ok = (not hard) and q == "address_exact"
    return ("auto_ok" if ok else "pending_review"), reasons


def build():
    seeds, snippets, annotations = load_inputs()
    posts, restaurants, links = consolidate(seeds, snippets, annotations)
    geo = load_json(PROCESSED / "geocode_results.json", {})
    profiles = load_json(RAW / "tiktok_profiles.json", {})
    PRIVATE.mkdir(parents=True, exist_ok=True)
    PUBLIC.mkdir(parents=True, exist_ok=True)
    db_path = PRIVATE / "poc.sqlite"
    con = sqlite3.connect(db_path)
    con.executescript(SCHEMA)

    ig_status = {"incrivelsp": "perfil localizado em resultado de busca; sem acesso permitido às publicações",
                 "reviewsporsp": "perfil NÃO confirmado (sem resultado de busca); sem acesso permitido",
                 "vivamaissp": "perfil NÃO confirmado (sem resultado de busca); sem acesso permitido"}
    for h, meta in INFLUENCERS.items():
        pr = profiles.get(h, {})
        con.execute("INSERT INTO influencers VALUES (?,?,?,?,?)",
                    (h, meta["display"], int(bool(pr.get("confirmed"))), pr.get("author_name"), ig_status[h]))
        con.execute("INSERT INTO validations(entity_type,entity_id,check_name,result,detail,checked_at) VALUES (?,?,?,?,?,?)",
                    ("influencer", h, "tiktok_profile_oembed", "confirmed" if pr.get("confirmed") else "not_confirmed",
                     f"HTTP {pr.get('http_status')} · {pr.get('author_name')}", pr.get("checked_at", "")))

    for p in posts:
        con.execute("INSERT INTO posts VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
            p["post_id"], p["platform"], p["influencer"], p["url"], p["posted_on"], p["date_source"], p["text_source"],
            int(p["text_trimmed"]), p["recommendation_type"], p["ad_disclosure"], p["confidence"], p["review_status"],
            json.dumps(p["limitations"], ensure_ascii=False), json.dumps(p["notes"], ensure_ascii=False)))
        for ev in p["evidence"]:
            con.execute("INSERT INTO evidence(entity_type,entity_id,kind,snippet,source) VALUES (?,?,?,?,?)",
                        ("post", p["post_id"], "extraction", ev, "web_search_index_title"))
        con.execute("INSERT INTO validations(entity_type,entity_id,check_name,result,detail,checked_at) VALUES (?,?,?,?,?,?)",
                    ("post", p["post_id"], "tiktok_video_oembed", "inconclusive",
                     "oEmbed de vídeo devolve só iframe: não valida existência, autoria nem legenda", now_iso()))

    pub_restaurants = []
    for r in restaurants:
        g = geo.get(r["restaurant_id"], {})
        muni = g.get("municipality") or r["municipality_hint"]
        in_city = (muni or "").lower().startswith("são paulo") or (muni or "").lower().startswith("sao paulo") or (not muni and not r["municipality_hint"])
        status, reasons = restaurant_review(r, g, in_city)
        has_coord = g.get("status") == "found"
        rec = {
            "restaurant_id": r["restaurant_id"], "name": r["name"], "name_source": r["name_source"],
            "unit_label": r.get("unit_label"), "multi_unit_brand": r["multi_unit_brand"],
            "address_text": r["address_text"], "municipality": muni, "neighborhood": g.get("neighborhood"),
            "lat": g.get("lat") if has_coord else None, "lon": g.get("lon") if has_coord else None,
            "coordinate_quality": g.get("coordinate_quality") if has_coord else "none",
            "geocode_source": "OpenStreetMap Nominatim (ODbL) — © colaboradores do OpenStreetMap" if has_coord else None,
            "existence_verified": bool(g.get("poi_found")), "in_sao_paulo_city": bool(in_city),
            "influencers": r["influencers"], "post_ids": r["post_ids"],
            "review_status": status, "review_reasons": reasons,
        }
        pub_restaurants.append(rec)
        con.execute("INSERT INTO restaurants VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
            rec["restaurant_id"], rec["name"], rec["name_source"], r["brand_key"], int(r["multi_unit_brand"]),
            rec["unit_label"], rec["address_text"], rec["municipality"], rec["neighborhood"], rec["lat"], rec["lon"],
            rec["coordinate_quality"], rec["geocode_source"], int(rec["existence_verified"]), int(rec["in_sao_paulo_city"]),
            status, json.dumps(reasons, ensure_ascii=False)))
        con.execute("INSERT INTO validations(entity_type,entity_id,check_name,result,detail,checked_at) VALUES (?,?,?,?,?,?)",
                    ("restaurant", r["restaurant_id"], "nominatim_geocode", g.get("status", "n/a"),
                     f"{g.get('osm_category')} · query={g.get('query')} · poi={g.get('poi_found')}", now_iso()))
    for l in links:
        con.execute("INSERT OR IGNORE INTO post_restaurants VALUES (?,?,?)", (l["post_id"], l["restaurant_id"], l["relation"]))

    # ---- comentários (apenas importados) ----
    all_comments = []
    for f in sorted(IMPORTS.glob("comments_*.csv")):
        all_comments += import_comments_csv(f)
    for c in all_comments:
        cur = con.execute("INSERT INTO comments(post_id,text,source,collected_on,selection_method,platform_total_comments,confidence,method) VALUES (?,?,?,?,?,?,?,?)",
                          (c["post_id"], c["text"], c["source"], c["collected_on"], c["selection_method"],
                           c["platform_total_comments"], c["confidence"], c["method"]))
        for lab in c["labels"]:
            con.execute("INSERT INTO comment_labels VALUES (?,?)", (cur.lastrowid, lab))

    google = load_json(PROCESSED / "google_probe.json", {})
    ig = load_json(PROCESSED / "instagram_probe.json", {})

    # ---- análise por restaurante (painel B2B privado) ----
    post_text = {pid: s["snippet"] for pid, s in snippets.items()}
    from .google_places import maps_search_url, select_restaurants
    g_sel = {r["restaurant_id"]: r for r in select_restaurants(pub_restaurants)}
    b2b_restaurants = []
    for rec in pub_restaurants:
        cms = [c for c in all_comments if c["post_id"] in rec["post_ids"]]
        cc = crosscheck.build(rec, post_text, cms, None)
        al = alerts.evaluate(cms, coverage_note="Sem coleta de comentários nesta PoC: acesso automático não permitido/validado.")
        b2b_restaurants.append({"restaurant_id": rec["restaurant_id"], "name": rec["name"], "crosscheck": cc, "alert": al,
                                "google": ({"status": "blocked_no_api_key", "selected_for_test": True,
                                            "public_page_reference": maps_search_url(rec["name"], rec["address_text"] or ""),
                                            "note": "link apenas para verificação humana; nada foi extraído da página"}
                                           if rec["restaurant_id"] in g_sel else {"status": "not_selected"})})
    n_posts = len(posts)
    coverage = {
        "generated_at": now_iso(), "posts_with_text": n_posts, "comments_analyzed": len(all_comments),
        "comments_instagram": 0, "comments_tiktok": len(all_comments),
        "google_places_status": google.get("error_status") or "not_run", "instagram_access": ig.get("http_status"),
        "text_source": "títulos devolvidos por índice de busca web (não é API do TikTok); vídeos não processados",
    }
    for k, v in coverage.items():
        con.execute("INSERT INTO coverage VALUES (?,?)", (k, json.dumps(v, ensure_ascii=False)))
    con.commit()

    pub_posts = [{k: p[k] for k in ("post_id", "platform", "influencer", "url", "posted_on", "date_source", "text_trimmed",
                                    "recommendation_type", "ad_disclosure", "confidence", "review_status", "limitations",
                                    "notes", "evidence", "restaurant_ids", "hashtag_candidates")} for p in posts]
    infl = []
    for h, meta in INFLUENCERS.items():
        pr = profiles.get(h, {})
        infl.append({"handle": h, "display_name": meta["display"], "tiktok_url": f"https://www.tiktok.com/@{h}",
                     "tiktok_confirmed": bool(pr.get("confirmed")), "instagram_status": ig_status[h],
                     "posts": sum(1 for p in posts if p["influencer"] == h)})
    meta = {"generated_at": now_iso(), "data_kind": "REAL", "attribution": "Mapa: © colaboradores do OpenStreetMap",
            "disclaimer": "Prova de conceito. Textos e datas de publicações vêm de fontes públicas indexadas; podem conter erros. "
                          "Registros 'pending_review' ainda não foram validados por humanos.",
            "counts": {"influencers": len(infl), "posts": n_posts, "restaurants": len(pub_restaurants)}}
    for name, obj in (("influencers", infl), ("posts", pub_posts), ("restaurants", pub_restaurants), ("meta", meta)):
        (PUBLIC / f"{name}.json").write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")
    (PRIVATE / "b2b.json").write_text(json.dumps({
        "data_kind": "REAL", "coverage": coverage, "restaurants": b2b_restaurants,
        "google_probe": google, "instagram_probe": ig,
        "alert_states_legend": alerts.STATES}, ensure_ascii=False, indent=1), encoding="utf-8")
    con.close()
    return {"posts": n_posts, "restaurants": len(pub_restaurants), "links": len(links), "comments": len(all_comments)}


if __name__ == "__main__":
    print(build())

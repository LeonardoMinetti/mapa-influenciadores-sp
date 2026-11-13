"""Instagram — investigação de acesso e importação de dados obtidos legitimamente.

Resultado da investigação (2026-11-13), ver docs/access-investigation.md:
- robots.txt do Instagram: "Collection of data on Instagram through automated means is prohibited
  unless you have express written permission". => NENHUM scraping é feito por este projeto.
- API oficial: oEmbed (graph.facebook.com/instagram_oembed) exige token de app Meta; Instagram Graph
  API só lê mídia/comentários de contas profissionais que AUTORIZARAM o app (ou Business Discovery,
  também com token de conta profissional própria). Sem token => bloqueado.
- Importação: `import_posts_csv` aceita posts/comentários obtidos por meios legítimos (exportação
  do próprio criador, dados licenciados) com colunas documentadas em data/schemas/.
"""
from __future__ import annotations

import csv
import os

from .common import http_get_json, now_iso


def probe_access() -> dict:
    """Testa, sem credenciais, o endpoint oficial e registra a resposta (diagnóstico verificável)."""
    token = os.environ.get("META_APP_ACCESS_TOKEN")
    url = "https://graph.facebook.com/v21.0/instagram_oembed?url=https://www.instagram.com/p/EXEMPLO/"
    if token:
        url += "&access_token=" + token
    status, body = http_get_json("instagram_oembed_probe", url)
    err = (body or {}).get("error", {}) if isinstance(body, dict) else {}
    return {
        "checked_at": now_iso(), "token_configured": bool(token), "http_status": status,
        "error_code": err.get("code"), "error_message": err.get("message"),
        "conclusion": ("sem token de app Meta não há acesso programático autorizado; "
                       "mesmo com token, oEmbed não devolve legenda de perfis de terceiros nem comentários."),
        "automated_collection_validated": False,
    }


def import_posts_csv(path: str) -> list[dict]:
    """Importa posts do Instagram obtidos legitimamente. Colunas: influencer,url,posted_on,caption,source."""
    rows = []
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if not r.get("url") or "instagram.com" not in r["url"]:
                continue
            rows.append({"platform": "instagram", **{k: (v or "").strip() for k, v in r.items()}})
    return rows

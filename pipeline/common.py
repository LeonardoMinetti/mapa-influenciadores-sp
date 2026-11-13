"""Utilitários compartilhados: caminhos, HTTP com log de chamadas (para o relatório de custos)."""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RAW = DATA / "raw"
LOGS = DATA / "logs"
PRIVATE = DATA / "private"      # NÃO versionado: texto de terceiros, SQLite, painel B2B real
PROCESSED = DATA / "processed"  # versionado: derivados sem texto de terceiros (geocodificação, diagnósticos)
PUBLIC = DATA / "public"
SEEDS = DATA / "seeds"
IMPORTS = DATA / "imports"

# User-Agent genérico: sem dados pessoais (regra do projeto).
USER_AGENT = "mapa-influenciadores-sp-poc/0.1 (research proof of concept)"

INFLUENCERS = {
    "reviewsporsp": {"display": "Reviews por SP (Bia e Clara)"},
    "incrivelsp": {"display": "Incrível SP (Amanda e Léo)"},
    "vivamaissp": {"display": "Viva Mais SP"},
}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def log_call(service: str, url: str, status: int, seconds: float, note: str = "") -> None:
    """Registra cada chamada externa (contagem de chamadas, erros, latência)."""
    LOGS.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": now_iso(),
        "service": service,
        "url": url.split("?")[0] if service == "google_places" else url,
        "status": status,
        "seconds": round(seconds, 3),
        "note": note,
    }
    with open(LOGS / "api_calls.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def http_get_json(service: str, url: str, headers: dict | None = None, retries: int = 2,
                  timeout: int = 25):
    """GET com User-Agent genérico, repetição limitada e log. Retorna (status, json|None)."""
    h = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    h.update(headers or {})
    last_status = 0
    for attempt in range(retries + 1):
        t0 = time.time()
        try:
            req = urllib.request.Request(url, headers=h)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body = r.read().decode("utf-8", "replace")
                log_call(service, url, r.status, time.time() - t0, f"attempt={attempt + 1}")
                return r.status, json.loads(body)
        except urllib.error.HTTPError as e:
            last_status = e.code
            body = ""
            try:
                body = e.read().decode("utf-8", "replace")
            except Exception:
                pass
            log_call(service, url, e.code, time.time() - t0, f"attempt={attempt + 1}")
            if e.code in (400, 401, 403, 404):  # não adianta repetir
                try:
                    return e.code, json.loads(body)
                except Exception:
                    return e.code, None
        except Exception as e:  # rede/timeout
            last_status = 0
            log_call(service, url, 0, time.time() - t0, f"attempt={attempt + 1} err={type(e).__name__}")
        time.sleep(1.5 * (attempt + 1))
    return last_status, None

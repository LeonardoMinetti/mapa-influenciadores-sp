"""Alerta privado de percepção de confiança (painel B2B) — critérios documentados em docs/alert-criteria.md.

Estados: no_relevant_signals | attention | recurring_questions | insufficient_data

Regras (todas devem ser atendidas para os estados 'attention'/'recurring_questions'):
- Só conta comentários ANALISADOS com rótulo `questiona_publicidade` ou `questiona_autenticidade`
  (confiança média/alta). Publicidade declarada, concentração de campanhas ou nº de posts NUNCA contam.
- Piso de amostra: >= MIN_COMMENTS comentários analisados nas publicações do restaurante; abaixo => insufficient_data.
- attention: >= 1 manifestação e < RECURRING_N; recurring_questions: >= RECURRING_N manifestações E
  >= RECURRING_SHARE do total analisado, em >= 2 publicações OU >= 5 manifestações.
- Nenhuma classificação alarmista; o texto sempre traz evidências, limitações e sugestões práticas.
"""
from __future__ import annotations

MIN_COMMENTS = 10
RECURRING_N = 3
RECURRING_SHARE = 0.10

STATES = {
    "no_relevant_signals": "Sem sinais relevantes identificados",
    "attention": "Atenção à percepção de confiança",
    "recurring_questions": "Questionamentos recorrentes",
    "insufficient_data": "Dados insuficientes",
}

SUGGESTIONS = {
    "attention": [
        "Responder com transparência às dúvidas nos comentários (ex.: informar se a visita foi convite/parceria).",
        "Pedir que parceiros usem a marcação de publicidade da plataforma de forma visível.",
    ],
    "recurring_questions": [
        "Alinhar com o influenciador uma comunicação clara de parceria e do que foi cortesia.",
        "Publicar informações verificáveis (cardápio, preços, horários) para reduzir dúvidas.",
        "Incentivar relatos de clientes reais (avaliações no Google) além do conteúdo patrocinado.",
    ],
    "no_relevant_signals": ["Manter o monitoramento; não há ação recomendada com base nestes dados."],
    "insufficient_data": ["Ampliar a amostra de comentários legitimamente obtidos antes de qualquer conclusão."],
}


def evaluate(comments: list[dict], posts_with_comments: int | None = None, coverage_note: str = "") -> dict:
    n = len(comments)
    flagged = [c for c in comments
               if c.get("confidence") in ("medium", "high")
               and ({"questiona_publicidade", "questiona_autenticidade"} & set(c.get("labels", [])))]
    posts = {c["post_id"] for c in flagged}
    limitations = [
        "Comentários de espectadores não são avaliações de clientes que visitaram o local.",
        "Classificação por regras léxicas (baseline); sujeita a erros de ironia e contexto.",
    ]
    if coverage_note:
        limitations.append(coverage_note)
    if n < MIN_COMMENTS:
        state = "insufficient_data"
    elif len(flagged) >= RECURRING_N and len(flagged) / n >= RECURRING_SHARE and (len(posts) >= 2 or len(flagged) >= 5):
        state = "recurring_questions"
    elif len(flagged) >= 1:
        state = "attention"
    else:
        state = "no_relevant_signals"
    return {
        "state": state, "label": STATES[state], "comments_analyzed": n, "flagged_comments": len(flagged),
        "flagged_posts": len(posts), "evidence_examples": [c["text"][:140] for c in flagged[:3]],
        "context": "Manifestações de espectadores em publicações de influenciadores (não é avaliação de cliente).",
        "limitations": limitations, "suggestions": SUGGESTIONS[state],
        "criteria": f"mín. {MIN_COMMENTS} comentários; recorrente = ≥{RECURRING_N} manifestações e ≥{int(RECURRING_SHARE*100)}% do total",
    }

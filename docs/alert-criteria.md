# Alerta privado de percepção de confiança — critérios

Implementação: `pipeline/alerts.py` (testada em `tests/test_comments_alerts.py`). Apenas painel B2B privado; **nunca** no mapa público.

| Estado | Condição |
|---|---|
| Dados insuficientes | < 10 comentários analisados nas publicações do restaurante |
| Sem sinais relevantes identificados | ≥ 10 analisados e 0 manifestações de dúvida sobre publicidade/autenticidade |
| Atenção à percepção de confiança | ≥ 10 analisados e 1–2 manifestações (ou ≥ 3 mas abaixo de 10 % / só 1 publicação com < 5) |
| Questionamentos recorrentes | ≥ 3 manifestações, ≥ 10 % do total, e (≥ 2 publicações **ou** ≥ 5 manifestações) |

- "Manifestação" = comentário classificado com `questiona_publicidade` ou `questiona_autenticidade` com confiança média/alta (≥ 2 pistas léxicas).
- **Publicidade declarada, número de posts ou concentração de campanhas nunca entram no cálculo.**
- Cada alerta traz: evidências (trechos), contagem, contexto, limitações e sugestões práticas. Sem linguagem alarmista.
- Comentário de espectador ≠ avaliação de cliente.
- **Estado real nesta PoC: todos "Dados insuficientes"** (0 comentários coletados). Os quatro estados só aparecem no painel com dados fictícios rotulados (demo).

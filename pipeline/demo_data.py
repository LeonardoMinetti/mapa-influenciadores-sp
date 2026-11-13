"""Dados FICTÍCIOS (demonstração de interface + testes). Nunca misturar com dados reais.

Restaurantes e comentários aqui são inventados de propósito e rotulados 'FICTÍCIO'. As classificações
e os alertas, porém, são produzidos pelo código real (classify + alerts.evaluate + crosscheck.build).
"""
from __future__ import annotations

import json

from . import alerts, crosscheck
from .common import DATA
from .comments import classify, scrub

DEMO_COMMENTS = {
    "A": [  # volume suficiente, sem questionamentos
        "Amei esse lugar, parece uma delícia!", "Onde fica? Qual o horário?", "Vou ir no sábado, anotado",
        "Fui semana passada, a comida estava ótima mesmo", "Quanto custa o rodízio?", "Perfeito, salvei aqui",
        "Quero conhecer, bora marcar", "Que lindo o ambiente", "Aceita VR?", "Já fui e recomendo muito",
        "Preço bom para o que entrega", "Top demais!",
    ],
    "B": [  # alguns questionamentos pontuais
        "Isso é publi né? Parece propaganda", "Amei, vou ir!", "Onde fica?", "Fui mês passado e demorou muito para atender",
        "Parece caro, quanto é?", "Show de bola", "Quero ir com a família", "Que delícia", "Qual unidade?",
        "Fomos lá e o garçom foi muito simpático", "Salvei pra ir", "Maravilhoso",
    ],
    "C": [  # questionamentos recorrentes em duas publicações
        "Isso é publi? Sempre os mesmos lugares", "Parece tudo combinado, não confio muito",
        "Foi pago pra falar bem né", "Amei o prato!", "Onde fica?", "Mentira, fui e não é isso tudo",
        "Propaganda disfarçada", "Que caro, R$ 199", "Vou ir conhecer", "Parece fake essa recomendação",
        "Perfeito", "Fui ontem, atendimento ruim",
    ],
    "D": ["Amei!", "Onde fica?", "Vou ir"],  # amostra insuficiente
}


def build_demo() -> dict:
    restaurants = []
    for key, texts in DEMO_COMMENTS.items():
        rid = f"demo_{key.lower()}"
        pids = [f"demo_post_{key}1", f"demo_post_{key}2"]
        cms = []
        for i, t in enumerate(texts):
            c = classify(scrub(t))
            cms.append({"post_id": pids[i % 2], "text": t, **c})
        rest = {"restaurant_id": rid, "post_ids": pids}
        post_text = {pids[0]: "FICTÍCIO: atendimento rápido, preço bom e ambiente lindo",
                     pids[1]: "FICTÍCIO: comida incrível, rodízio com ótimo custo-benefício"}
        cc = crosscheck.build(rest, post_text, cms, {"status": "ok", "theme_counts": {"atendimento": 2, "tempo_espera": 3}}
                              if key == "B" else None)
        al = alerts.evaluate(cms, coverage_note="DEMONSTRAÇÃO com comentários fictícios.")
        restaurants.append({"restaurant_id": rid, "name": f"Restaurante Fictício {key}", "crosscheck": cc, "alert": al,
                            "google": {"status": "demo_only"}})
    return {"data_kind": "DEMO", "banner": "DADOS FICTÍCIOS — apenas demonstração de interface. Nenhum restaurante, comentário ou alerta abaixo é real.",
            "coverage": {"comments_analyzed": sum(len(v) for v in DEMO_COMMENTS.values()), "comments_instagram": 0,
                         "comments_tiktok": 0, "google_places_status": "demo", "text_source": "fictício"},
            "restaurants": restaurants, "google_probe": {"note": "demo"}, "instagram_probe": {"note": "demo"},
            "alert_states_legend": alerts.STATES}


def main():
    d = build_demo()
    out = DATA / "demo"
    out.mkdir(parents=True, exist_ok=True)
    (out / "b2b_demo.json").write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    return [(r["name"], r["alert"]["state"]) for r in d["restaurants"]]


if __name__ == "__main__":
    print(main())

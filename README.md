# Mapa de Influenciadores SP — prova de conceito

PoC para avaliar a viabilidade de uma plataforma com (1) **mapa gratuito** de restaurantes recomendados por influenciadores
gastronômicos de São Paulo e (2) **painel B2B privado** de inteligência de reputação para restaurantes.
Escopo fixo: `@reviewsporsp`, `@incrivelsp`, `@vivamaissp`.

- **Site (mapa + revisão + painel demo):** https://leonardominetti.github.io/mapa-influenciadores-sp/
- **Relatório final com métricas, custos e o que falhou:** [docs/relatorio-final.md](docs/relatorio-final.md)
- **Investigação de acesso às plataformas:** [docs/access-investigation.md](docs/access-investigation.md)

## Resultado em uma tabela (execução real de 13/11/2026)

| Meta | Resultado |
|---|---|
| Publicações (meta 60) | **42** com texto público obtido por **índice de busca web** — **0 via API oficial** (o oEmbed de vídeo do TikTok não devolve legenda) |
| Restaurantes | **34 unidades** (32 marcas); **33** com coordenadas OSM, só **15** de endereço exato; **2** confirmados como POI no OSM |
| Comentários (meta 270) | **0** — coleta automática não permitida/validada (TikTok Research API é acadêmica; Instagram exige autorização do criador) |
| Instagram | **0** publicações (robots.txt proíbe coleta automatizada; sem token Meta) |
| Google (5 restaurantes) | **Bloqueado** — HTTP 403 sem chave/faturamento; código pronto e travado; nenhum dado obtido/simulado |
| Análises cruzadas | **0** possíveis (faltam 2 das 3 fontes) |
| Alerta de confiança | Implementado e testado; no dado real todos = *Dados insuficientes* |
| Custo cobrado | **US$ 0** |

Leia o relatório antes de tirar conclusões: a PoC prova a **cadeia técnica** (publicação → restaurante → coordenada → mapa → revisão) e prova
que **os dados de comentários e avaliações não são obteníveis de forma permitida com a infraestrutura atual**.

## Estrutura

```
pipeline/   Python (stdlib apenas): coleta, extração, consolidação, geocodificação, comentários, Google, cruzamento, alertas, métricas
web/        React + Vite + Leaflet: Mapa, Revisão manual, Painel B2B
data/       seeds/ (URLs), public/ (JSON derivado, publicado), processed/ (geocodificação, diagnósticos), schemas/, demo/ (FICTÍCIO), logs/
tests/      35 testes (unittest) incl. integridade dos dados públicos
docs/       investigação de acesso, módulo Google, critérios do alerta, relatório final
review/     auditoria interna + local para suas correções exportadas
.github/    workflows: publicar Pages (push) e pipeline manual (testes)
```

## Rodar

```bash
python3 -m unittest discover -s tests -t . -v      # testes
cd web && npm ci && npm run build                  # site público (painel B2B = demo fictício)
npm run dev                                        # local: painel B2B com dados REAIS privados (requer data/private/)
```

Pipeline completo (requer `data/private/search_snippets.json`, **não versionado** por ser texto de terceiros):
`python3 -m pipeline.run_pipeline` (reexecução usa cache em `data/raw/`).
Para importar comentários/posts obtidos legitimamente: ver [data/schemas/comments_import.md](data/schemas/comments_import.md).
Variáveis opcionais em [.env.example](.env.example).

## Privacidade e termos

- Nenhum token ou dado pessoal versionado; comentários (quando importados) perdem autor, @menções, e-mails e telefones.
- O repositório publica **campos derivados** (restaurante, endereço, link da publicação, flags), não legendas nem comentários.
- Painel B2B com dados reais **não** é publicado (sem autenticação segura). A página pública usa **dados fictícios rotulados**.
- Mapa: © colaboradores do OpenStreetMap (ODbL) e base cinza minimalista da Esri (sem chave; uso gratuito limitado — para produto comercial, contratar provedor de tiles).
- Datas das publicações são **derivadas do ID do vídeo** (não vêm de API).

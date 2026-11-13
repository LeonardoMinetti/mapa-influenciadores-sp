# Módulo Google Maps — avaliações

**Estado: implementado e travado. Nenhum dado Google foi coletado** (sem chave de API e sem autorização de faturamento).

## Diagnóstico verificável
`python3 -c "from pipeline import google_places as g; print(g.probe())"` → `POST places.googleapis.com/v1/places:searchText` sem chave:
**HTTP 403 `PERMISSION_DENIED`** (arquivo `data/processed/google_probe.json`, log em `data/logs/api_calls.jsonl`).

## Cinco restaurantes selecionados (determinístico, `select_restaurants`)
Capital de SP + coordenada de endereço exato + maior nº de publicações, no máximo 2 por influenciador:
Legado Parrilla, Carola Restobar, Mamma Concetta, Burgguers Tatuapé, Chico Grill.
No painel local cada um traz um link do Google Maps **só para verificação humana** — nada é requisitado nem extraído da página.

## O que o código faz quando houver chave + autorização
`fetch_place()` faz 1 *Text Search* (campos `rating`, `userRatingCount`, `reviews`) e recusa rodar sem `GOOGLE_MAPS_API_KEY`
**e** sem `--authorize-billing`. Persiste apenas `place_id`, nota, contagem total, nº de avaliações devolvidas e **contagem por tema**
(comida, atendimento, tempo de espera, preço, ambiente, experiência geral); o texto das avaliações fica só em memória.

## Perguntas da investigação
1. **Públicas sem API?** Nome, endereço e nota aparecem no navegador, mas isso não autoriza copiar em massa.
2. **API oficial sem dono?** Places API (New): dados do lugar, `rating`, `userRatingCount` e até **5 avaliações selecionadas** — campos de avaliação em SKU pago (Enterprise); exige faturamento (documentação; não foi possível testar sem chave).
3. **Avaliações via Places?** No máximo 5 por lugar, escolhidas pelo Google: **não** são o histórico nem amostra representativa e nunca devem ser apresentadas como tal.
4. **Scraping/armazenamento:** os termos do Google Maps Platform proíbem extração automatizada e restringem cache/armazenamento de conteúdo (apenas `place_id` pode ser guardado indefinidamente) e exigem atribuição. Não implementado.
5. **Exige o proprietário:** histórico completo de avaliações, respostas e métricas → **Business Profile API** com OAuth do dono.

> Preço de tabela verificado em 13/11/2026 (tabela oficial, páginas de terceiros concordam): Text Search com campos de avaliação cai na faixa **Enterprise + Atmosphere ≈ US$ 40 por 1.000 chamadas**, com **1.000 chamadas gratuitas por mês por SKU** — os 5 testes caberiam na cota gratuita, mas **o faturamento precisa estar habilitado no projeto**. Confirme sempre na página oficial antes de autorizar gasto.

## Próximos passos (precisam de você)
1. Criar projeto no Google Cloud, habilitar Places API (New) e definir **teto de orçamento/alerta**.
2. Gerar chave restrita e colocar em `.env` (`GOOGLE_MAPS_API_KEY`).
3. Autorizar explicitamente o gasto; rodar com `--authorize-billing` nos 5 restaurantes (5 chamadas Text Search).

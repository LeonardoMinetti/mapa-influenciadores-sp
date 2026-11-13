# Relatório final da prova de conceito — 13/11/2026

> Tudo abaixo vem de execução real. Números são calculados por `pipeline/metrics.py` (arquivo `data/public/metrics.json`).
> Onde algo não foi possível, está escrito como **não calculável** ou **bloqueado**.

## 1. Veredito de viabilidade

| Pergunta | Resposta honesta |
|---|---|
| Dá para montar o **mapa de consumidores** a partir de publicações de influenciadores? | **Sim, tecnicamente** (publicação → restaurante → endereço → coordenada → mapa → revisão funciona de ponta a ponta). **Mas** a origem do texto nesta PoC (índice de busca web) **não é uma base comercial sustentável**. |
| Dá para obter **comentários** (Instagram/TikTok) de forma permitida e automática? | **Não** com a infraestrutura atual: 0 comentários. Exige adesão/autorização dos criadores, API licenciada ou dados de parceiros. |
| Dá para obter **avaliações do Google** sem o dono? | **Só até 5 avaliações selecionadas por lugar** via Places API (paga, não testada por falta de chave). Histórico completo → Business Profile API com **autorização do restaurante** (o que combina com o modelo B2B). |
| O **cruzamento promessa × audiência × clientes** foi demonstrado? | **Não com dados reais** (0 análises possíveis). O código e a regra de "hipótese, nunca conclusão" estão implementados e testados. |

## 2. Indicadores (seção 13 do briefing)

| Indicador | Resultado real |
|---|---|
| Publicações tentadas | **42** (meta 60; descoberta limitada pela busca web) — por perfil: {'incrivelsp': 11, 'reviewsporsp': 9, 'vivamaissp': 22} |
| Publicações recuperadas | **42** com texto público via índice de busca; **0 via API oficial** (oEmbed de vídeo devolve só iframe) |
| Recomendações identificadas | **17** explícitas (avaliação positiva no texto) + 7 visita/vitrine + 7 só menção = **33** publicações com restaurante identificado; 11 sem restaurante identificável no texto |
| Restaurantes únicos | **34** unidades (32 marcas; 2 redes com 2 unidades) |
| Locais geolocalizados | **33** com coordenadas; **15** de endereço exato, 16 aproximadas (rua), 2 de área; 1 rejeitada (logradouro homônimo em outro município) |
| Existência confirmada em fonte | **2** (POI de mesmo nome no OSM) — as demais **não têm existência verificada** |
| Recomendações duplicadas | **1** consolidada (Mamma Concetta: 2 posts, 2 grafias de @, mesmo endereço) |
| Comentários Instagram | **0** |
| Comentários TikTok | **0** |
| Restaurantes testados no Google | **5 selecionados; 0 consultados** (bloqueado: HTTP 403 sem chave/faturamento) |
| Avaliações Google acessíveis legitimamente | **0** |
| Análises cruzadas possíveis | **0** |
| Taxa de erros identificados | Ver §4 — **não há taxa humana independente ainda** |
| Custo total da execução | **US$ 0,00 cobrado** (nenhum serviço pago usado) |
| Tempo total | ≈ **17 min** de relógio desde o 1º comando até este relatório (inclui desenvolvimento). Etapas de rede: oEmbed 42 chamadas ≈ 43 s; Nominatim ≈ 104 s (1 req/s) |

Não calculáveis hoje: taxa de erro real (precisa de revisão humana), cobertura de comentários, convergência/divergência entre fontes, custo por restaurante com Google, custo de vídeo (vídeos não foram processados).

## 3. O que funcionou, falhou e ficou bloqueado

**Funcionou**
- Confirmação de identidade dos 3 perfis no TikTok (oEmbed de criador).
- Descoberta de 42 URLs reais de vídeos + legendas (parciais) pela busca; extração de restaurante/endereço/publicidade por regras.
- Consolidação (duplicatas, unidades distintas da mesma rede), geocodificação OSM com **rejeição de homônimos** e checagem de coerência de bairro.
- Repositório e site no ar: https://github.com/LeonardoMinetti/mapa-influenciadores-sp · https://leonardominetti.github.io/mapa-influenciadores-sp/ (200 OK, mapa renderiza 33 marcadores).
- Mapa, revisão manual com exportação, painel B2B (real local / demo fictício), alerta com 4 estados, 35 testes.

**Falhou**
- oEmbed de vídeo do TikTok **não valida** existência, autoria nem legenda (retorna 200 para ID inexistente e para @ errado).
- Perfil `@reviewsporsp`: só 9 publicações achadas (muitas sem nome de restaurante no texto — o conteúdo está no vídeo, **não processado**).
- Instagram: perfis de `@reviewsporsp` e `@vivamaissp` nem foram localizados na busca.

**Bloqueado (decisão deliberada, por termos/credenciais)**
- Scraping de Instagram/TikTok (robots.txt proíbe) — **não executado**.
- Comentários (nenhum caminho permitido sem autorização).
- Google Places (sem chave; gastos exigem sua autorização).

## 4. Qualidade e auditoria

Auditoria **interna** (Claude, leitura dos textos + checagens automáticas; `review/claude_audit.json`) — não é auditoria humana independente:
- Identidade do restaurante: 35 vínculos publicação→restaurante (33 publicações) conferidos contra o texto → **0 erros** no resultado final. Antes das correções de desenvolvimento a extração tinha erros em ≈ 14 das 42 publicações (hashtags tomadas por nome, rótulo de unidade tomado por nome, endereços com lixo, rua homônima em outro município); todos corrigidos e cobertos por testes.
- Geocodificação: 15 exatas; 16 só no nível da rua; **4 com bairro divergente** do texto; 1 rejeitada. Essas ficam em *validação pendente*.
- Revisão humana necessária: **20 de 34 restaurantes (59 %)** e **13 de 42 publicações (31 %)**.
- Limites: "recomendação" e "publicidade" dependem de textos às vezes truncados; **ausência de marcação ≠ ausência de publicidade** (por isso o campo se chama `not_detected_in_available_text`). Só 5 publicações trazem marcação explícita.

## 5. Custos e eficiência (operação ≠ desenvolvimento)

| Item | Observado |
|---|---|
| Ferramentas | Python stdlib, OSM Nominatim, TikTok oEmbed, busca web (ferramenta da sessão), React/Vite/Leaflet, GitHub Pages/Actions — todas gratuitas aqui |
| Chamadas de API (log) | 129 no total: oEmbed vídeo 42, oEmbed perfil 6, Nominatim 77, sonda Instagram 2 (400 esperado), sonda Google 2 (403 esperado) |
| Busca web | 13 consultas (não faturadas separadamente) |
| Erros / novas tentativas | 0 erros inesperados, 0 retentativas; 4 "erros" são as sondas de bloqueio, intencionais |
| Tokens | **Pipeline: 0** (regras determinísticas). A leitura/anotação por Claude ocorreu na sessão; **tokens não mensuráveis aqui** e cobertos pela assinatura (não contam como 2ª cobrança) |
| Custo cobrado | **US$ 0** |
| Vídeo | Não processado. É o maior custo/risco futuro (transcrição + visão) |
| Validação manual | 20 restaurantes + 13 publicações pendentes |

## 6. Extrapolação para 50 influenciadores (**estimativas**, não custos observados)

Premissas (derivadas desta PoC): 20 posts/influenciador → 1.000 posts; 0,8 restaurante/post → ≈ 800; 2,3 chamadas de geocodificação por restaurante.

| Item | Estimativa | Natureza |
|---|---|---|
| Descoberta de posts | A busca web rendeu ≈ 3 posts/consulta → ≈ 300 consultas, **frágil e não reprodutível**; produto real precisa de fonte contratada/autorizada | Inviável como está |
| Geocodificação OSM | ≈ 1.850 chamadas ≈ 35 min a 1 req/s; em escala comercial usar instância própria/provedor (custo de infra, ordem de dezenas de US$/mês) | Estimativa |
| Google Places | ≈ 800 Text Searches de campos Enterprise; a preço de tabela da ordem de US$ 30–40 por mil ⇒ **≈ US$ 25–35 por atualização completa** (confirmar preços e cotas gratuitas atuais; **não verificado hoje**) | Estimativa |
| LLM (identificação + comentários) | ≈ 2 M de tokens no total (1.000 posts + ≈ 4.500 comentários) ⇒ **poucos dólares** a preços de modelos pequenos | Estimativa de volume |
| Vídeo (se necessário) | transcrição de ≈ 1.000 vídeos de ~1 min: ordem de **dezenas de dólares** + risco de termos | Estimativa grosseira |
| Revisão humana | com as taxas observadas (59 % dos restaurantes, 31 % das publicações) ≈ 470 + 310 itens ≈ **13 h** a ~1 min/item | Extrapolação do observado |
| Hospedagem | GitHub Pages grátis para o mapa; painel B2B exige autenticação/hospedagem própria | — |

**O custo dominante não é computacional: é acesso legítimo a dados** (comentários, Instagram, avaliações completas).

## 7. Próximos passos — o que depende de você

1. **Revisar** na página *Revisão manual* os casos incertos e exportar as correções (gera a taxa de erro real).
2. **Google**: criar projeto/chave com teto de orçamento e **autorizar** os 5 chamados (`docs/google-module.md`).
3. **Comentários/Instagram**: decidir o caminho — (a) adesão dos criadores via OAuth (Instagram Graph / TikTok Login Kit), (b) CSV exportado pelos próprios criadores, (c) fornecedor de dados com contrato claro. Há importador pronto.
4. Para o B2B: restaurantes conectando o **próprio** Google Business Profile e Instagram profissional é o caminho de dados **permitido e mais rico** — vale validar com 2–3 restaurantes piloto.
5. (Concluído) GitHub Actions ativado após autorização do escopo `workflow`; o site é publicado pelo workflow `pages.yml`.
6. Trocar os tiles gratuitos (CARTO/OSM) por provedor contratado antes de qualquer tráfego real.

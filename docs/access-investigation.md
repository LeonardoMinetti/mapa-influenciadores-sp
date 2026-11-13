# Investigação de acesso aos dados (executada em 13/11/2026)

Tudo abaixo foi **testado nesta execução** (comandos registrados em `data/logs/api_calls.jsonl`) ou está marcado como
"documentação, não testado".

## 1. Perfis

| Perfil | TikTok | Instagram |
|---|---|---|
| `@reviewsporsp` | **confirmado** via oEmbed oficial de criador (`author_name` = "BIA E CLARA") | **não confirmado** (nenhum resultado de busca para o perfil) |
| `@incrivelsp` | **confirmado** ("Incrivelsp") | perfil localizado em resultado de busca: "Amanda e Léo – Incrivel São Paulo (@incrivelsp)" (~1 M seguidores segundo o snippet) |
| `@vivamaissp` | **confirmado** ("vivamaissp") | **não confirmado** |

Atenção a homônimos: `@reviewssporsp` (dois "s") e `@biaerafareviews` apareceram nas buscas e **foram excluídos**.

## 2. TikTok

| Método | Resultado | Decisão |
|---|---|---|
| `robots.txt` | `User-agent: *` só permite um conjunto pequeno de caminhos (`/foryou`, `/discover`, `/about`…); páginas de perfil não estão na lista; crawlers de IA (inclui ClaudeBot) são proibidos | **Não raspar** páginas de perfil/vídeo |
| oEmbed de **perfil** (`/oembed?url=…/@handle`) | HTTP 200, devolve nome do criador | Usado para confirmar identidade |
| oEmbed de **vídeo** | HTTP 200 mas **só devolve um `<iframe>`** (sem título/legenda/autor). Teste com ID inexistente e com `@handle` errado: **mesma resposta 200** | **Inútil como validação** de existência/autoria/legenda. Registrado como "inconclusivo" |
| Research API | Documentação: restrita a pesquisadores acadêmicos/sem fins comerciais (não testado — sem credencial) | Inviável para produto comercial |
| Display API / Login Kit | Documentação: só lê o conteúdo do próprio usuário que autoriza o app | Possível apenas com **adesão do criador** |
| Comentários | Sem endpoint público permitido | **Bloqueado** |

**O que foi realmente usado para obter as publicações:** descoberta de URLs e dos *títulos* (que no TikTok são as legendas)
pelo **índice de busca web** (ferramenta de busca, 7 consultas, restritas a `tiktok.com`). É texto de terceiros indexado
publicamente, **não** é uma API do TikTok, é limitado (títulos às vezes truncados), não reprodutível por nós e **não
é base adequada para um produto comercial**. Por isso o texto fica em `data/private/` (não versionado) e o repositório
publica só campos derivados.

## 3. Instagram

- `robots.txt` do Instagram declara que a coleta automatizada é proibida sem permissão escrita da Meta e referencia os
  "Automated Data Collection Terms". **Nenhum scraping foi executado.**
- oEmbed oficial (`graph.facebook.com/instagram_oembed`) **sem token** → HTTP 400 `OAuthException` (testado). Mesmo com token de app,
  oEmbed não devolve legenda de terceiros em volume nem comentários.
- Graph API (documentação, não testado): lê mídia e comentários apenas de contas profissionais que **autorizam o app**;
  *Business Discovery* exige token de uma conta profissional própria e só devolve métricas agregadas (ex.: `comments_count`), não o texto de comentários de terceiros.
- **Resultado:** 0 publicações e 0 comentários do Instagram. Caminho de produto: programa de adesão dos criadores (OAuth) ou dados licenciados.
  Há importação por CSV (`pipeline/instagram.py`, `data/schemas/comments_import.md`).

## 4. Google

Ver `docs/google-module.md`. Resumo: chamada sem credencial → **403 PERMISSION_DENIED** (registrada). Nada foi coletado nem simulado.

## 5. OpenStreetMap / Nominatim (geocodificação)

Uso permitido (ODbL, atribuição obrigatória). Política respeitada: ≤ 1 requisição/s, User-Agent identificado
(genérico), cache em disco. 77 chamadas. Para escala comercial, usar instância própria ou provedor contratado.
Tiles do mapa: servidor padrão do OSM com atribuição — adequado para a PoC, **não** para tráfego comercial.

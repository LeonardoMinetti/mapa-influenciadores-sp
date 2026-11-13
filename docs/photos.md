# Fotos dos restaurantes

**Estado (13/11/2026): nenhuma foto de restaurante foi adicionada ao mapa**, por não haver fonte automática com licença clara.
O que existe hoje em cada ficha é o **vídeo da indicação** pelo player oficial de incorporação do TikTok (clique em *Ver vídeo*).

## O que foi testado
| Fonte | Resultado |
|---|---|
| Wikimedia Commons (busca pelo nome dos 32 restaurantes) | 0 fotos utilizáveis (só falsos positivos, ex.: "MEET Iso Omena") |
| oEmbed do TikTok | Vídeo devolve apenas iframe: sem imagem de capa |
| Player oficial `tiktok.com/player/v1/<id>` em iframe | **Funciona** (testado no site publicado) — usado como visual |

## O que não foi feito (por direitos autorais/termos)
Copiar fotos do Google Maps/Places (só com chave e sem armazenar), do Instagram dos restaurantes ou de sites de terceiros.

## Como entram fotos (manifesto `data/public/photos.json`)
Cada foto precisa de **crédito + licença/autorização**:
1. **Fornecida pelo restaurante ou criador** — `pipeline.photos.add_manual(restaurant_id, arquivo, crédito, licença)`.
2. **Mapillary (fachada, CC BY-SA 4.0)** — `pipeline.photos.fetch_mapillary(restaurantes)` com `MAPILLARY_ACCESS_TOKEN` (gratuito). Código escrito, escolha da imagem testada, **chamada à API não testada** (sem token).
3. **Google Places Photos** — só com chave + faturamento autorizado; fora do escopo atual.

O site lê o manifesto e mostra a foto com o crédito; sem foto, mostra o cartão de cor do influenciador com a inicial.

# CSV de importação de comentários (`data/imports/comments_*.csv`)

Para comentários obtidos **legitimamente** (exportação do próprio criador, API autorizada, dado licenciado).

| coluna | obrigatória | descrição |
|---|---|---|
| `post_id` | sim | ID do vídeo (igual a `posts.json`) |
| `text` | sim | texto do comentário (e-mails, telefones e @menções são removidos na importação) |
| `source` | não | origem (ex.: `export_do_criador`, `graph_api_autorizada`) |
| `collected_on` | não | data da coleta |
| `method` | não | método de seleção (ex.: `primeiros_30_por_relevancia`) — obrigatório registrar |
| `platform_total_comments` | não | total informado pela plataforma |

Colunas de autor/usuário/foto **são ignoradas de propósito** (minimização de dados). Máximo de 30 comentários por publicação.
Esses arquivos não são versionados (`.gitignore`), exceto os `exemplo_*.csv`.

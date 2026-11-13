# Arquivos de revisão

- `claude_audit.json` — auditoria interna feita por Claude (leitura dos textos + checagens automáticas). **Não** substitui revisão humana.
- Exporte suas correções pela página **Revisão manual** do site (botões *Exportar JSON/CSV*) e salve aqui como `correcoes-revisao.json` / `.csv`.
  Formato do JSON: `{"exported_at": "...", "items": {"<post_id|restaurant_id>": {"decision": "confirmed|corrected|error", "name": "...", "address": "...", "notes": "..."}}}`.

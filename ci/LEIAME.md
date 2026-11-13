# Workflows do GitHub Actions (pendentes de ativação)

O token do GitHub CLI usado na criação do repositório **não tinha o escopo `workflow`**, então o push de
`.github/workflows/*` foi recusado pelo GitHub. Os arquivos estão aqui, prontos e revisados:

- `pages.yml` — build do site e publicação no GitHub Pages (a cada push em `web/**` ou `data/public/**`, ou manual).
- `pipeline.yml` — execução **manual** (sem agendamento) dos testes Python.

Para ativar:

```bash
gh auth refresh -h github.com -s workflow     # autoriza o escopo no navegador
mkdir -p .github/workflows && git mv ci/pages.yml ci/pipeline.yml .github/workflows/
git commit -m "Ativa workflows" && git push
# Em Settings > Pages, trocar a fonte de "Deploy from a branch" para "GitHub Actions".
```

Enquanto isso, o site é publicado a partir da branch `gh-pages` (build gerado com `cd web && npm run build`).

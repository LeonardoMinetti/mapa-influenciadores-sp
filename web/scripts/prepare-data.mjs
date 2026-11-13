// Copia os dados para web/public/data.
// - Dados REAIS públicos (derivados): data/public/*.json  -> sempre.
// - Painel B2B: com PRIVATE_DATA=1 usa data/private/b2b.json (REAL, só ambiente local);
//   caso contrário usa data/demo/b2b_demo.json (FICTÍCIO). O build público nunca recebe o arquivo privado.
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..')
const out = path.resolve(root, 'web/public/data')
fs.rmSync(out, { recursive: true, force: true })
fs.mkdirSync(out, { recursive: true })
for (const f of ['influencers', 'posts', 'restaurants', 'meta']) {
  fs.copyFileSync(path.join(root, 'data/public', `${f}.json`), path.join(out, `${f}.json`))
}
const priv = process.env.PRIVATE_DATA === '1'
const src = priv ? 'data/private/b2b.json' : 'data/demo/b2b_demo.json'
fs.copyFileSync(path.join(root, src), path.join(out, 'b2b.json'))
console.log(`[prepare-data] painel B2B: ${priv ? 'REAL (local)' : 'DEMO fictício'}`)

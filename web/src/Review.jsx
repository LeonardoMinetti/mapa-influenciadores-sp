import React, { useEffect, useMemo, useState } from 'react'
import { QUALITY_LABEL, REC_LABEL, fmtDate } from './data.js'

const KEY = 'mapa-sp-poc-review-v1'
const load = () => {
  try { return JSON.parse(localStorage.getItem(KEY) || '{}') } catch { return {} }
}
const DECISIONS = [
  ['', 'Sem revisão'],
  ['confirmed', 'Confirmado'],
  ['corrected', 'Corrigido'],
  ['error', 'Erro (descartar)'],
]

function download(name, text, type) {
  const url = URL.createObjectURL(new Blob([text], { type }))
  const a = Object.assign(document.createElement('a'), { href: url, download: name })
  a.click()
  URL.revokeObjectURL(url)
}
const csvCell = (v) => `"${String(v ?? '').replace(/"/g, '""')}"`

export default function Review({ data }) {
  const { posts, restaurants } = data
  const [tab, setTab] = useState('posts')
  const [onlyUncertain, setOnlyUncertain] = useState(true)
  const [store, setStore] = useState(load)
  const restById = useMemo(() => Object.fromEntries(restaurants.map((r) => [r.restaurant_id, r])), [restaurants])

  useEffect(() => {
    try { localStorage.setItem(KEY, JSON.stringify(store)) } catch { /* sem storage */ }
  }, [store])
  const set = (id, patch) => setStore((s) => ({ ...s, [id]: { ...(s[id] || {}), ...patch } }))

  const postItems = posts.map((p) => {
    const reasons = []
    if (p.review_status !== 'auto_ok') reasons.push('identificação pendente')
    if (p.confidence === 'low' || p.confidence === 'none') reasons.push(`confiança ${p.confidence}`)
    if (p.text_trimmed) reasons.push('texto reduzido na fonte')
    if (!p.restaurant_ids.length) reasons.push('sem restaurante')
    if (p.recommendation_type === 'mention_only' || p.recommendation_type === 'visit_showcase') reasons.push('recomendação ambígua')
    const uncertain = p.review_status !== 'auto_ok' || p.confidence === 'low' || !p.restaurant_ids.length
    return { id: p.post_id, p, reasons, score: reasons.length + (uncertain ? 10 : 0), uncertain }
  })
  const restItems = restaurants.map((r) => ({
    id: r.restaurant_id, r, reasons: r.review_reasons,
    score: r.review_reasons.length + (r.review_status !== 'auto_ok' ? 10 : 0), uncertain: r.review_status !== 'auto_ok',
  }))
  const items = (tab === 'posts' ? postItems : restItems)
    .filter((i) => !onlyUncertain || i.uncertain)
    .sort((a, b) => b.score - a.score)
  const reviewed = Object.values(store).filter((v) => v.decision).length

  const exportJson = () =>
    download('correcoes-revisao.json', JSON.stringify({ exported_at: new Date().toISOString(), items: store }, null, 1), 'application/json')
  const exportCsv = () => {
    const rows = [['entity_id', 'decision', 'corrected_name', 'corrected_address', 'notes']]
    Object.entries(store).forEach(([id, v]) => v.decision && rows.push([id, v.decision, v.name, v.address, v.notes]))
    download('correcoes-revisao.csv', rows.map((r) => r.map(csvCell).join(',')).join('\n'), 'text/csv')
  }

  return (
    <div className="page">
      <h1>Revisão manual</h1>
      <p className="muted">
        Os registros mais incertos aparecem primeiro. Suas decisões ficam apenas neste navegador; exporte para enviar as correções.
        Nada é enviado a servidor.
      </p>
      <div className="toolbar">
        <div className="tabs">
          <button className={tab === 'posts' ? 'on' : ''} onClick={() => setTab('posts')}>Publicações ({posts.length})</button>
          <button className={tab === 'rest' ? 'on' : ''} onClick={() => setTab('rest')}>Restaurantes ({restaurants.length})</button>
        </div>
        <label className="check">
          <input type="checkbox" checked={onlyUncertain} onChange={(e) => setOnlyUncertain(e.target.checked)} /> Só casos incertos
        </label>
        <span className="muted">{reviewed} revisados</span>
        <button onClick={exportJson}>Exportar JSON</button>
        <button onClick={exportCsv}>Exportar CSV</button>
      </div>

      <div className="rows">
        {items.map(({ id, p, r, reasons }) => {
          const v = store[id] || {}
          return (
            <section className={'row ' + (v.decision || '')} key={id}>
              <div className="rowmain">
                {p ? (
                  <>
                    <h3>@{p.influencer} · {fmtDate(p.posted_on)}</h3>
                    <p><a href={p.url} target="_blank" rel="noopener noreferrer">Abrir publicação original ↗</a></p>
                    <p>
                      Restaurante identificado:{' '}
                      <strong>{p.restaurant_ids.map((x) => restById[x]?.name).join(', ') || '— nenhum —'}</strong>
                    </p>
                    <p className="muted">{REC_LABEL[p.recommendation_type]} · confiança {p.confidence}</p>
                    {p.evidence.length > 0 && <p className="muted">Evidências: {p.evidence.join(' · ')}</p>}
                    {p.notes.map((n) => <p className="muted" key={n}>Nota: {n}</p>)}
                  </>
                ) : (
                  <>
                    <h3>{r.name}</h3>
                    <p>{r.address_text || 'sem endereço'}</p>
                    <p className="muted">
                      {[r.neighborhood, r.municipality].filter(Boolean).join(' · ')} · {QUALITY_LABEL[r.coordinate_quality]}
                      {r.lat != null && (
                        <> · <a target="_blank" rel="noopener noreferrer" href={`https://www.openstreetmap.org/?mlat=${r.lat}&mlon=${r.lon}#map=18/${r.lat}/${r.lon}`}>ver no OSM ↗</a></>
                      )}
                    </p>
                    <p className="muted">{r.post_ids.length} publicação(ões) · {r.influencers.map((h) => '@' + h).join(', ')}</p>
                  </>
                )}
                {reasons.length > 0 && <ul className="why">{reasons.map((x) => <li key={x}>{x}</li>)}</ul>}
              </div>
              <div className="rowform">
                <label>Decisão
                  <select value={v.decision || ''} onChange={(e) => set(id, { decision: e.target.value })}>
                    {DECISIONS.map(([k, l]) => <option key={k} value={k}>{l}</option>)}
                  </select>
                </label>
                <label>Nome correto
                  <input value={v.name || ''} onChange={(e) => set(id, { name: e.target.value })} placeholder={r ? r.name : ''} />
                </label>
                <label>Endereço correto
                  <input value={v.address || ''} onChange={(e) => set(id, { address: e.target.value })} />
                </label>
                <label>Observações
                  <textarea rows="2" value={v.notes || ''} onChange={(e) => set(id, { notes: e.target.value })} />
                </label>
              </div>
            </section>
          )
        })}
        {items.length === 0 && <p className="pad">Nenhum registro neste filtro.</p>}
      </div>
    </div>
  )
}

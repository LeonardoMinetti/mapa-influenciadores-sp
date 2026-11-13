import { useEffect, useState } from 'react'

const base = import.meta.env.BASE_URL
async function load(name) {
  const r = await fetch(`${base}data/${name}.json`)
  if (!r.ok) throw new Error(`${name}: HTTP ${r.status}`)
  return r.json()
}

export function useData() {
  const [state, setState] = useState({ loading: true })
  useEffect(() => {
    Promise.all(['influencers', 'posts', 'restaurants', 'meta'].map(load))
      .then(([influencers, posts, restaurants, meta]) => setState({ influencers, posts, restaurants, meta }))
      .catch((error) => setState({ error: String(error) }))
  }, [])
  return state
}

export function useB2B() {
  const [state, setState] = useState({ loading: true })
  useEffect(() => {
    load('b2b').then((b2b) => setState({ b2b })).catch((error) => setState({ error: String(error) }))
  }, [])
  return state
}

export const REC_LABEL = {
  recommendation: 'Recomendação explícita',
  visit_showcase: 'Visita / vitrine (sem avaliação explícita no texto)',
  mention_only: 'Apenas menção',
  unknown: 'Restaurante não identificado',
}
export const QUALITY_LABEL = {
  address_exact: 'Endereço exato',
  street_approx: 'Aproximada (rua)',
  area: 'Área (parque/praia)',
  none: 'Sem coordenadas',
}
export const INFL_COLOR = { reviewsporsp: '#d1495b', incrivelsp: '#2e86ab', vivamaissp: '#3b9b5c' }
export const fmtDate = (s) => (s ? s.split('-').reverse().join('/') : '')

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
      .then(async ([influencers, posts, restaurants, meta]) => {
        // fotos são opcionais: só entram fontes com licença/autorização registrada (ver docs/photos.md)
        const photos = await load('photos').catch(() => ({}))
        setState({ influencers, posts, restaurants, meta, photos })
      })
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
  visit_showcase: 'Visita / vitrine',
  mention_only: 'Apenas menção',
  unknown: 'Restaurante não identificado',
}
export const QUALITY_LABEL = {
  address_exact: 'Endereço exato',
  street_approx: 'Localização aproximada',
  area: 'Área (parque/praia)',
  none: 'Sem coordenadas',
}
export const INFL_COLOR = { reviewsporsp: '#FF5C8A', incrivelsp: '#2D7FF9', vivamaissp: '#12B76A' }
export const INFL_SHORT = { reviewsporsp: 'Reviews por SP', incrivelsp: 'Incrível SP', vivamaissp: 'Viva Mais SP' }
export const fmtDate = (s) => (s ? s.split('-').reverse().join('/') : '')

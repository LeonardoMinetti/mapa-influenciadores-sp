import React, { useEffect, useState } from 'react'
import { useData } from './data.js'
import MapView from './MapView.jsx'
import Review from './Review.jsx'
import Panel from './Panel.jsx'

const PRIVATE = import.meta.env.VITE_PRIVATE === '1'
const routeOf = () => (location.hash.replace('#/', '') || 'mapa').split('?')[0]

export default function App() {
  const [route, setRoute] = useState(routeOf())
  const data = useData()
  useEffect(() => {
    const f = () => setRoute(routeOf())
    window.addEventListener('hashchange', f)
    return () => window.removeEventListener('hashchange', f)
  }, [])
  const tabs = [
    ['mapa', 'Mapa'],
    ['revisao', 'Revisão manual'],
    ['painel', PRIVATE ? 'Painel B2B (local)' : 'Painel B2B (demo fictício)'],
  ]
  return (
    <div className="app">
      <header className="top">
        <div className="brand">
          <strong>Mapa de Influenciadores SP</strong>
          <span className="poc">Prova de conceito</span>
        </div>
        <nav aria-label="Seções">
          {tabs.map(([k, label]) => (
            <a key={k} href={`#/${k}`} className={route === k ? 'active' : ''} aria-current={route === k ? 'page' : undefined}>
              {label}
            </a>
          ))}
        </nav>
      </header>
      <main>
        {data.loading && <p className="pad">Carregando dados…</p>}
        {data.error && <p className="pad error">Erro ao carregar dados: {data.error}</p>}
        {data.restaurants && route === 'mapa' && <MapView data={data} />}
        {data.restaurants && route === 'revisao' && <Review data={data} />}
        {route === 'painel' && <Panel data={data} />}
      </main>
    </div>
  )
}

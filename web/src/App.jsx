import React, { useEffect, useState } from 'react'
import { useData } from './data.js'
import MapView from './MapView.jsx'
import Review from './Review.jsx'
import Panel from './Panel.jsx'
import { IconCheck, IconChart, IconPin } from './Icons.jsx'

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
    ['mapa', 'Mapa', <IconPin key="i" />],
    ['revisao', 'Revisão', <IconCheck key="i" />],
    ['painel', PRIVATE ? 'Painel B2B' : 'Painel B2B (demo)', <IconChart key="i" />],
  ]
  return (
    <div className="app">
      <header className="top">
        <a className="logo" href="#/mapa" aria-label="Mapa SP — início">
          <span className="logo-dot" />
          <span className="logo-word">MAPA<b>SP</b></span>
          <span className="poc">PoC</span>
        </a>
        <nav aria-label="Seções">
          {tabs.map(([k, label, icon]) => (
            <a key={k} href={`#/${k}`} className={route === k ? 'active' : ''} aria-current={route === k ? 'page' : undefined}>
              {icon}
              <span>{label}</span>
            </a>
          ))}
        </nav>
      </header>
      <main>
        {data.loading && <p className="pad">Carregando…</p>}
        {data.error && <p className="pad error">Erro ao carregar dados: {data.error}</p>}
        {data.restaurants && route === 'mapa' && <MapView data={data} />}
        {data.restaurants && route === 'revisao' && <Review data={data} />}
        {route === 'painel' && <Panel data={data} />}
      </main>
    </div>
  )
}

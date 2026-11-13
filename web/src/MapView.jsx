import React, { useEffect, useMemo, useRef, useState } from 'react'
import L from 'leaflet'
import { INFL_COLOR, QUALITY_LABEL, REC_LABEL, fmtDate } from './data.js'

export default function MapView({ data }) {
  const { influencers, restaurants, posts, meta } = data
  const [selected, setSelected] = useState(() => new Set(influencers.map((i) => i.handle)))
  const [onlyConfirmed, setOnlyConfirmed] = useState(false)
  const [openId, setOpenId] = useState(null)
  const mapEl = useRef(null)
  const map = useRef(null)
  const layer = useRef(null)
  const postById = useMemo(() => Object.fromEntries(posts.map((p) => [p.post_id, p])), [posts])

  const visible = useMemo(
    () =>
      restaurants.filter(
        (r) => r.influencers.some((h) => selected.has(h)) && (!onlyConfirmed || r.review_status === 'auto_ok'),
      ),
    [restaurants, selected, onlyConfirmed],
  )
  const mapped = visible.filter((r) => r.lat != null)
  const unmapped = visible.filter((r) => r.lat == null)

  useEffect(() => {
    if (map.current) return
    map.current = L.map(mapEl.current, { zoomControl: true }).setView([-23.56, -46.64], 11)
    // Base cartográfica minimalista (Esri cinza claro/escuro, sem chave de API): poucas linhas, destaca só os marcadores.
    const dark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
    const esri = 'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas'
    const attribution =
      'Base: Esri, HERE, Garmin, © <a href="https://www.openstreetmap.org/copyright">colaboradores do OpenStreetMap</a>'
    L.tileLayer(`${esri}/${dark ? 'World_Dark_Gray_Base' : 'World_Light_Gray_Base'}/MapServer/tile/{z}/{y}/{x}`, {
      maxZoom: 19, maxNativeZoom: 16, attribution,
    }).addTo(map.current)
    L.tileLayer(`${esri}/${dark ? 'World_Dark_Gray_Reference' : 'World_Light_Gray_Reference'}/MapServer/tile/{z}/{y}/{x}`, {
      maxZoom: 19, maxNativeZoom: 16,
    }).addTo(map.current)
    layer.current = L.layerGroup().addTo(map.current)
  }, [])

  useEffect(() => {
    if (!layer.current) return
    layer.current.clearLayers()
    mapped.forEach((r) => {
      const color = INFL_COLOR[r.influencers[0]] || '#555'
      const exact = r.coordinate_quality === 'address_exact'
      const m = L.circleMarker([r.lat, r.lon], {
        radius: exact ? 10 : 9,
        color,
        weight: 3,
        opacity: 0.95,
        fillColor: color,
        fillOpacity: exact ? 0.85 : 0.1,
        dashArray: exact ? null : '3 3',
      })
      m.bindTooltip(r.name)
      m.on('click', () => setOpenId(r.restaurant_id))
      m.addTo(layer.current)
    })
  }, [mapped])

  const open = restaurants.find((r) => r.restaurant_id === openId)

  const toggle = (h) =>
    setSelected((s) => {
      const n = new Set(s)
      n.has(h) ? n.delete(h) : n.add(h)
      return n
    })

  return (
    <div className="mapwrap">
      <aside className="side">
        <h2>Influenciadores</h2>
        <div className="chips" role="group" aria-label="Filtrar influenciadores">
          {influencers.map((i) => (
            <button
              key={i.handle}
              className={'chip' + (selected.has(i.handle) ? ' on' : '')}
              style={{ '--c': INFL_COLOR[i.handle] }}
              onClick={() => toggle(i.handle)}
              aria-pressed={selected.has(i.handle)}
            >
              <span className="dot" /> @{i.handle}
              <small>{i.posts} posts</small>
            </button>
          ))}
        </div>
        <label className="check">
          <input type="checkbox" checked={onlyConfirmed} onChange={(e) => setOnlyConfirmed(e.target.checked)} />
          Ocultar registros com validação pendente
        </label>
        <p className="muted">
          {mapped.length} no mapa · {unmapped.length} sem coordenadas confiáveis · {visible.filter((r) => r.review_status !== 'auto_ok').length} com validação pendente
        </p>
        <p className="legend">
          <span className="sw solid" /> endereço exato &nbsp; <span className="sw dashed" /> aproximado / pendente
        </p>

        {open ? (
          <article className="card">
            <button className="close" onClick={() => setOpenId(null)} aria-label="Fechar ficha">×</button>
            <h3>{open.name}</h3>
            {open.unit_label && <p className="muted">Unidade: {open.unit_label}</p>}
            <p>{open.address_text || 'Endereço não informado na publicação'}</p>
            <p className="muted">
              {[open.neighborhood, open.municipality].filter(Boolean).join(' · ')} · {QUALITY_LABEL[open.coordinate_quality]}
            </p>
            {open.review_status !== 'auto_ok' && (
              <div className="pending">
                <strong>Validação pendente</strong>
                <ul>{open.review_reasons.map((x) => <li key={x}>{x}</li>)}</ul>
              </div>
            )}
            <h4>Indicado por</h4>
            {open.post_ids.map((id) => {
              const p = postById[id]
              return (
                <div className="post" key={id}>
                  <span className="tag" style={{ background: INFL_COLOR[p.influencer] }}>@{p.influencer}</span>
                  <div>
                    <a href={p.url} target="_blank" rel="noopener noreferrer">Abrir publicação no TikTok ↗</a>
                    <div className="muted">
                      {fmtDate(p.posted_on)} <abbr title="Data derivada do ID do vídeo">(derivada)</abbr> · {REC_LABEL[p.recommendation_type]}
                    </div>
                    {p.ad_disclosure === 'declared' ? (
                      <span className="badge ad">Publicidade declarada</span>
                    ) : (
                      <span className="badge">Sem marcação de publicidade no texto disponível</span>
                    )}
                  </div>
                </div>
              )
            })}
          </article>
        ) : (
          <p className="muted">Clique em um marcador para abrir a ficha do estabelecimento.</p>
        )}

        {unmapped.length > 0 && (
          <details>
            <summary>{unmapped.length} sem coordenadas confiáveis</summary>
            <ul className="plain">
              {unmapped.map((r) => (
                <li key={r.restaurant_id}>
                  <button className="link" onClick={() => setOpenId(r.restaurant_id)}>{r.name}</button>
                </li>
              ))}
            </ul>
          </details>
        )}
        <p className="foot">{meta.disclaimer}</p>
      </aside>
      <div className="map" ref={mapEl} role="application" aria-label="Mapa de restaurantes" />
    </div>
  )
}

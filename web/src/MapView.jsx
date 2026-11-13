import React, { useEffect, useMemo, useRef, useState } from 'react'
import L from 'leaflet'
import { INFL_COLOR, INFL_SHORT, QUALITY_LABEL, REC_LABEL, fmtDate } from './data.js'
import { IconBack, IconExternal, IconHeart, IconPlay, IconSearch } from './Icons.jsx'

const SAVED_KEY = 'mapa-sp-poc-saved-v1'
const loadSaved = () => {
  try { return new Set(JSON.parse(localStorage.getItem(SAVED_KEY) || '[]')) } catch { return new Set() }
}
const initial = (name) => (name.match(/[A-Za-zÀ-ú0-9]/) || ['?'])[0].toUpperCase()

function Photo({ r, photo, size = 'card' }) {
  const c = INFL_COLOR[r.influencers[0]] || '#999'
  if (photo?.file) {
    return (
      <div className={`photo ${size}`}>
        <img src={`${import.meta.env.BASE_URL}${photo.file}`} alt={`Foto de ${r.name}`} loading="lazy" />
        <span className="credit">{photo.credit}</span>
      </div>
    )
  }
  return (
    <div className={`photo ${size} fallback`} style={{ '--c': c }} role="img" aria-label={`${r.name}: sem foto ainda`}>
      <span className="initial">{initial(r.name)}</span>
      <span className="nophoto">Sem foto ainda</span>
    </div>
  )
}

export default function MapView({ data }) {
  const { influencers, restaurants, posts, meta, photos } = data
  const [selected, setSelected] = useState(() => new Set(influencers.map((i) => i.handle)))
  const [hidePending, setHidePending] = useState(false)
  const [q, setQ] = useState('')
  const [openId, setOpenId] = useState(null)
  const [onlySaved, setOnlySaved] = useState(false)
  const [saved, setSaved] = useState(loadSaved)
  const [video, setVideo] = useState(null)
  const mapEl = useRef(null)
  const map = useRef(null)
  const layer = useRef(null)
  const colRef = useRef(null)
  const markers = useRef({})
  const postById = useMemo(() => Object.fromEntries(posts.map((p) => [p.post_id, p])), [posts])

  const visible = useMemo(() => {
    const t = q.trim().toLowerCase()
    return restaurants
      .filter((r) => r.influencers.some((h) => selected.has(h)))
      .filter((r) => !hidePending || r.review_status === 'auto_ok')
      .filter((r) => !onlySaved || saved.has(r.restaurant_id))
      .filter((r) => !t || `${r.name} ${r.neighborhood || ''} ${r.address_text || ''}`.toLowerCase().includes(t))
      .sort((a, b) => (a.review_status === 'auto_ok' ? 0 : 1) - (b.review_status === 'auto_ok' ? 0 : 1) || a.name.localeCompare(b.name))
  }, [restaurants, selected, hidePending, q, onlySaved, saved])
  const open = restaurants.find((r) => r.restaurant_id === openId)

  useEffect(() => {
    try { localStorage.setItem(SAVED_KEY, JSON.stringify([...saved])) } catch { /* sem storage */ }
  }, [saved])

  useEffect(() => {
    if (map.current) return
    map.current = L.map(mapEl.current, { zoomControl: false, maxZoom: 16 }).setView([-23.56, -46.64], 11)
    L.control.zoom({ position: 'bottomright' }).addTo(map.current)
    const esri = 'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas'
    L.tileLayer(`${esri}/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}`, {
      maxZoom: 16,
      attribution: 'Base: Esri, HERE, Garmin, © <a href="https://www.openstreetmap.org/copyright">colaboradores do OpenStreetMap</a>',
    }).addTo(map.current)
    L.tileLayer(`${esri}/World_Light_Gray_Reference/MapServer/tile/{z}/{y}/{x}`, { maxZoom: 12 }).addTo(map.current) // rótulos só em visão ampla (nível detalhado vem sem rótulo)
    layer.current = L.layerGroup().addTo(map.current)
  }, [])

  useEffect(() => {
    if (!layer.current) return
    layer.current.clearLayers()
    markers.current = {}
    visible.filter((r) => r.lat != null).forEach((r) => {
      const color = INFL_COLOR[r.influencers[0]] || '#555'
      const exact = r.coordinate_quality === 'address_exact'
      const isOpen = r.restaurant_id === openId
      const m = L.circleMarker([r.lat, r.lon], {
        radius: isOpen ? 12 : 8, color: isOpen ? '#171717' : '#fff', weight: isOpen ? 3 : 2,
        fillColor: color, fillOpacity: exact ? 0.95 : 0.35,
      })
      m.bindTooltip(r.name, { direction: 'top', offset: [0, -6] })
      m.on('click', () => selectRestaurant(r.restaurant_id))
      m.addTo(layer.current)
      if (isOpen) m.bringToFront()
      markers.current[r.restaurant_id] = m
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [visible, openId])

  function selectRestaurant(id) {
    setOpenId(id)
    setVideo(null)
    colRef.current?.scrollTo({ top: 0 })
    const r = restaurants.find((x) => x.restaurant_id === id)
    if (r?.lat != null && map.current) map.current.flyTo([r.lat, r.lon], Math.min(16, Math.max(map.current.getZoom(), 14)), { duration: 0.6 })
  }
  const toggle = (h) => setSelected((s) => { const n = new Set(s); n.has(h) ? n.delete(h) : n.add(h); return n })
  const toggleSave = (id) => setSaved((s) => { const n = new Set(s); n.has(id) ? n.delete(id) : n.add(id); return n })
  const mapped = visible.filter((r) => r.lat != null).length

  return (
    <div className="shell">
      <section className="col" ref={colRef}>
        {open ? (
          <article className="detail-view">
            <button className="back" onClick={() => { setOpenId(null); setVideo(null) }}>
              <IconBack /> Voltar para a lista
            </button>
            <Photo r={open} photo={photos?.[open.restaurant_id]} size="hero" />
            <h1 className="title">{open.name}</h1>
            {open.unit_label && <p className="kicker">Unidade {open.unit_label}</p>}
            <div className="tags">
              {open.influencers.map((h) => (
                <span className="tag solid" style={{ '--c': INFL_COLOR[h] }} key={h}>@{h}</span>
              ))}
              {open.neighborhood && <span className="tag">{open.neighborhood}</span>}
            </div>
            <button className={'save' + (saved.has(open.restaurant_id) ? ' on' : '')} onClick={() => toggleSave(open.restaurant_id)}>
              <IconHeart filled={saved.has(open.restaurant_id)} /> {saved.has(open.restaurant_id) ? 'Salvo' : 'Salvar'}
            </button>

            <h2 className="label">Endereço</h2>
            <p className="addr">
              {open.address_text || 'Endereço não informado na publicação'}
              {open.lat != null && (
                <>
                  {' '}
                  <a href={`https://www.google.com/maps/dir/?api=1&destination=${open.lat},${open.lon}`} target="_blank" rel="noopener noreferrer">
                    Abrir rota <IconExternal />
                  </a>
                </>
              )}
            </p>
            <p className="muted">{[open.municipality, QUALITY_LABEL[open.coordinate_quality]].filter(Boolean).join(' · ')}</p>

            {open.review_status !== 'auto_ok' && (
              <div className="notice">
                <strong>Validação pendente</strong>
                <ul>{open.review_reasons.map((x) => <li key={x}>{x}</li>)}</ul>
              </div>
            )}

            <h2 className="label">Quem indicou</h2>
            {open.post_ids.map((id) => {
              const p = postById[id]
              const showing = video === id
              return (
                <div className="indic" key={id}>
                  <div className="indic-head">
                    <span className="tag solid" style={{ '--c': INFL_COLOR[p.influencer] }}>@{p.influencer}</span>
                    <span className="muted">{fmtDate(p.posted_on)} <abbr title="Data derivada do ID do vídeo">(derivada)</abbr></span>
                  </div>
                  <p className="muted">{REC_LABEL[p.recommendation_type]}</p>
                  {p.ad_disclosure === 'declared'
                    ? <span className="badge ad">Publicidade declarada</span>
                    : <span className="badge">Sem marcação de publicidade no texto disponível</span>}
                  <div className="actions">
                    <button className="btn" onClick={() => setVideo(showing ? null : id)}>
                      <IconPlay /> {showing ? 'Fechar vídeo' : 'Ver vídeo'}
                    </button>
                    <a className="btn ghost" href={p.url} target="_blank" rel="noopener noreferrer">Abrir no TikTok <IconExternal /></a>
                  </div>
                  {showing && (
                    <iframe
                      className="player"
                      title={`Vídeo de @${p.influencer}`}
                      src={`https://www.tiktok.com/player/v1/${p.post_id}?music_info=1&description=1&autoplay=0`}
                      allow="fullscreen"
                      loading="lazy"
                    />
                  )}
                </div>
              )
            })}
          </article>
        ) : (
          <>
            <p className="tagline">Descubra onde os influenciadores gastronômicos de São Paulo comem.</p>
            <div className="chips" role="group" aria-label="Filtrar influenciadores">
              {influencers.map((i) => (
                <button key={i.handle} className={'chip' + (selected.has(i.handle) ? ' on' : '')} style={{ '--c': INFL_COLOR[i.handle] }}
                  onClick={() => toggle(i.handle)} aria-pressed={selected.has(i.handle)}>
                  <span className="avatar">{initial(INFL_SHORT[i.handle])}</span>
                  <span>@{i.handle}</span>
                </button>
              ))}
            </div>
            <label className="search">
              <IconSearch />
              <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Buscar restaurante, bairro ou rua" aria-label="Buscar" />
            </label>
            <div className="filters">
              <label className="switch"><input type="checkbox" checked={hidePending} onChange={(e) => setHidePending(e.target.checked)} /><span /> Só validados</label>
              <label className="switch"><input type="checkbox" checked={onlySaved} onChange={(e) => setOnlySaved(e.target.checked)} /><span /> Salvos ({saved.size})</label>
            </div>
            <h2 className="label">Restaurantes · {visible.length} <span className="muted">({mapped} no mapa)</span></h2>
            <div className="grid">
              {visible.map((r) => (
                <article className="card" key={r.restaurant_id}>
                  <button className="card-main" onClick={() => selectRestaurant(r.restaurant_id)}>
                    <Photo r={r} photo={photos?.[r.restaurant_id]} />
                    <h3>{r.name}</h3>
                    <div className="tags">
                      {r.influencers.map((h) => <span className="dotpill" style={{ '--c': INFL_COLOR[h] }} key={h}>{INFL_SHORT[h]}</span>)}
                      {r.neighborhood && <span className="tag">{r.neighborhood}</span>}
                      {r.review_status !== 'auto_ok' && <span className="tag warn">Pendente</span>}
                    </div>
                  </button>
                  <button className={'save small' + (saved.has(r.restaurant_id) ? ' on' : '')} onClick={() => toggleSave(r.restaurant_id)} aria-label={saved.has(r.restaurant_id) ? 'Remover dos salvos' : 'Salvar'}>
                    <IconHeart filled={saved.has(r.restaurant_id)} /> {saved.has(r.restaurant_id) ? 'Salvo' : 'Salvar'}
                  </button>
                </article>
              ))}
              {visible.length === 0 && <p className="muted">Nenhum restaurante neste filtro.</p>}
            </div>
            <p className="foot">{meta.disclaimer}</p>
          </>
        )}
      </section>
      <div className="map" ref={mapEl} role="application" aria-label="Mapa de restaurantes" />
    </div>
  )
}

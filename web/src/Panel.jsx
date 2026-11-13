import React, { useState } from 'react'
import { useB2B } from './data.js'

const PRIVATE = import.meta.env.VITE_PRIVATE === '1'
const TONE = { no_relevant_signals: 'ok', attention: 'warn', recurring_questions: 'alert', insufficient_data: 'gray' }
const THEME = {
  comida: 'Qualidade da comida', atendimento: 'Atendimento', tempo_espera: 'Tempo de espera',
  preco_custo_beneficio: 'Preço e custo-benefício', ambiente: 'Ambiente', experiencia_geral: 'Experiência geral',
}
const SRC = { promise: 'Promessa do influenciador', audience: 'Reação da audiência', customers_google: 'Experiência dos clientes (Google)' }

export default function Panel({ data }) {
  const { b2b, error, loading } = useB2B()
  const [openId, setOpenId] = useState(null)
  if (loading) return <p className="pad">Carregando…</p>
  if (error) return <p className="pad error">{error}</p>
  const demo = b2b.data_kind === 'DEMO'
  const cov = b2b.coverage
  const rows = [...b2b.restaurants]
    .filter((r) => demo || r.alert.state !== 'insufficient_data' || r.google.selected_for_test)
    .sort((a, b) => a.name.localeCompare(b.name))
  const open = b2b.restaurants.find((r) => r.restaurant_id === openId)
  const total = b2b.restaurants.length

  return (
    <div className="page">
      <h1>Painel B2B experimental</h1>
      {demo ? (
        <div className="banner demo">{b2b.banner} Os dados reais do painel ficam apenas no ambiente local (sem autenticação segura não são publicados).</div>
      ) : (
        <div className="banner priv">Ambiente LOCAL — dados reais privados. Não publicar este build.</div>
      )}
      <div className="cards">
        <div className="stat"><b>{total}</b><span>restaurantes</span></div>
        <div className="stat"><b>{cov.comments_analyzed}</b><span>comentários realmente analisados</span></div>
        <div className="stat"><b>{cov.comments_instagram}</b><span>comentários Instagram</span></div>
        <div className="stat"><b>{demo ? 'demo' : (b2b.google_probe.error_status || '—')}</b><span>módulo Google</span></div>
      </div>
      <h2>Cobertura e limitações</h2>
      <ul>
        <li>Fonte do texto das publicações: {cov.text_source}.</li>
        {!demo && (
          <>
            <li>Comentários: coleta automática <strong>não permitida/validada</strong> (TikTok Research API é acadêmica; Instagram exige autorização do dono da conta). Há importação por CSV para dados obtidos legitimamente.</li>
            <li>Google: {b2b.google_probe.error_status} (HTTP {b2b.google_probe.http_status}) — sem chave de API/faturamento; nenhum dado foi obtido nem simulado.</li>
            <li>Instagram: HTTP {b2b.instagram_probe.http_status} no endpoint oficial sem token; scraping proibido pelo robots.txt.</li>
          </>
        )}
      </ul>
      <h2>Alertas privados de percepção de confiança</h2>
      <table>
        <thead><tr><th>Restaurante</th><th>Estado</th><th>Comentários analisados</th><th>Manifestações</th><th>Cruzamento</th></tr></thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.restaurant_id} onClick={() => setOpenId(r.restaurant_id)} className="click">
              <td><button className="link" onClick={() => setOpenId(r.restaurant_id)}>{r.name}</button></td>
              <td><span className={'state ' + TONE[r.alert.state]}>{r.alert.label}</span></td>
              <td>{r.alert.comments_analyzed}</td>
              <td>{r.alert.flagged_comments}</td>
              <td>{r.crosscheck.status === 'cross_analysis_possible' ? 'possível' : r.crosscheck.status === 'partial_two_sources' ? 'parcial (2 fontes)' : 'fontes insuficientes'}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {!demo && <p className="muted">Mostrando {rows.length} de {total}: restaurantes sem nenhum dado além da publicação foram omitidos da tabela; todos permanecem em “Dados insuficientes”.</p>}

      {open && (
        <article className="detail">
          <button className="close" onClick={() => setOpenId(null)} aria-label="Fechar">×</button>
          <h3>{open.name}</h3>
          <p><span className={'state ' + TONE[open.alert.state]}>{open.alert.label}</span></p>
          <p><b>Evidência:</b> {open.alert.flagged_comments} manifestação(ões) de {open.alert.comments_analyzed} comentários analisados ({open.alert.flagged_posts} publicação(ões)).</p>
          {open.alert.evidence_examples.length > 0 && <ul>{open.alert.evidence_examples.map((e) => <li key={e}>“{e}”</li>)}</ul>}
          <p><b>Contexto:</b> {open.alert.context}</p>
          <p className="muted"><b>Critério:</b> {open.alert.criteria}</p>
          <h4>Limitações</h4>
          <ul>{open.alert.limitations.map((x) => <li key={x}>{x}</li>)}</ul>
          <h4>Sugestões práticas</h4>
          <ul>{open.alert.suggestions.map((x) => <li key={x}>{x}</li>)}</ul>
          <h4>Cruzamento entre fontes</h4>
          <ul>
            {Object.entries(open.crosscheck.sources_available).map(([k, v]) => (
              <li key={k}>{SRC[k]}: {v ? 'disponível' : <b>indisponível</b>}</li>
            ))}
          </ul>
          {open.crosscheck.hypotheses.length === 0 && <p className="muted">Nenhuma hipótese: são necessárias ao menos duas perspectivas com evidência sobre o mesmo tema.</p>}
          {open.crosscheck.hypotheses.map((h) => (
            <p key={h.theme} className="hyp"><b>{THEME[h.theme]}:</b> {h.text}</p>
          ))}
          {open.google.public_page_reference && (
            <p className="muted">Referência de verificação humana: <a href={open.google.public_page_reference} target="_blank" rel="noopener noreferrer">buscar no Google Maps ↗</a> (nada foi extraído).</p>
          )}
        </article>
      )}
      {!PRIVATE && <p className="muted">Build público: este painel usa somente dados fictícios.</p>}
    </div>
  )
}

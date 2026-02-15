import { useState, useEffect } from 'react'
import api from '../api'
import RoomTimeGrid from './RoomTimeGrid'
import SlotDetail from './SlotDetail'

export default function Marketplace() {
  const [resources, setResources] = useState([])
  const [auctions, setAuctions] = useState([])
  const [agents, setAgents] = useState([])
  const [selectedAgent, setSelectedAgent] = useState(null)
  const [selectedSlot, setSelectedSlot] = useState(null)
  const [location, setLocation] = useState('')
  const [loading, setLoading] = useState(true)
  const [viewDate, setViewDate] = useState(new Date()) // Default to today

  const load = async () => {
    setLoading(true)
    try {
      // Calculate date range for the view (local time day)
      const start = new Date(viewDate)
      start.setHours(0, 0, 0, 0)
      const end = new Date(viewDate)
      end.setHours(23, 59, 59, 999)

      const [res, auc, ag] = await Promise.all([
        api.getResources(),
        api.getAuctions({ start_date: start.toISOString(), end_date: end.toISOString() }),
        api.getAgents(),
      ])
      setResources(res)
      setAuctions(auc)
      setAgents(ag)
      if (ag.length > 0 && !selectedAgent) setSelectedAgent(ag[0])
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  // Reload when date changes
  useEffect(() => { load() }, [viewDate])

  useEffect(() => {
    const handleAgentChange = () => {
      const id = localStorage.getItem('agent_id')
      if (id && agents.length > 0) {
        const a = agents.find(ag => ag.id === id)
        if (a) setSelectedAgent(a)
      }
    }
    window.addEventListener('agent-changed', handleAgentChange)
    return () => window.removeEventListener('agent-changed', handleAgentChange)
  }, [agents])

  const handleDateChange = (days) => {
    const next = new Date(viewDate)
    next.setDate(next.getDate() + days)
    setViewDate(next)
  }

  const locations = [...new Set(resources.map((r) => r.location).filter(Boolean))]
  const filtered = location
    ? resources.filter((r) => r.location === location)
    : resources

  const handleBuyNow = async (auction) => {
    if (!selectedAgent) return
    try {
      await api.placeBid(auction.id, {
        agent_id: selectedAgent.id,
        amount: auction.current_price,
      })
      await load()
      setSelectedSlot(null)
    } catch (e) {
      alert(e.message)
    }
  }

  const handleSetOrder = async (auction, maxPrice) => {
    if (!selectedAgent) return
    try {
      await api.createLimitOrder(auction.id, {
        agent_id: selectedAgent.id,
        max_price: maxPrice,
      })
      alert('Limit order placed')
    } catch (e) {
      alert(e.message)
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1>Marketplace</h1>
        <p>Browse available rooms and place bids on time slots</p>
      </div>

      <div className="filters-row" style={{ alignItems: 'flex-end' }}>
        <div className="form-group">
          <label>Date</label>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <button
              className="btn btn--small"
              onClick={() => handleDateChange(-1)}
            >&lt;</button>
            <div style={{
              background: 'white',
              padding: '0.5rem 1rem',
              border: '1px solid #ddd',
              borderRadius: '4px',
              fontWeight: 500,
              minWidth: '140px',
              textAlign: 'center'
            }}>
              {viewDate.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' })}
            </div>
            <button
              className="btn btn--small"
              onClick={() => handleDateChange(1)}
            >&gt;</button>
          </div>
        </div>

        <div className="form-group">
          <label>Location</label>
          <select value={location} onChange={(e) => setLocation(e.target.value)}>
            <option value="">All locations</option>
            {locations.map((l) => (
              <option key={l} value={l}>{l}</option>
            ))}
          </select>
        </div>

        {/* Sync with Global Agent Selector */}
        <div className="form-group">
          <label>Acting as (Global)</label>
          <select
            value={selectedAgent?.id || ''}
            onChange={(e) => {
              const a = agents.find((a) => a.id === e.target.value)
              if (a) {
                setSelectedAgent(a)
                localStorage.setItem('agent_id', a.id)
                window.dispatchEvent(new Event('agent-changed'))
              }
            }}
          >
            {agents.map((a) => (
              <option key={a.id} value={a.id}>{a.name} ({a.token_balance.toFixed(1)} tokens)</option>
            ))}
          </select>
        </div>
      </div>

      {loading ? (
        <div className="text-secondary" style={{ padding: '2rem' }}>Loading schedule...</div>
      ) : filtered.length === 0 ? (
        <div className="card text-secondary" style={{ padding: '3rem', textAlign: 'center' }}>
          No rooms available. An admin needs to create rooms.
        </div>
      ) : (
        <RoomTimeGrid
          resources={filtered}
          auctions={auctions}
          selectedSlot={selectedSlot}
          onSelectSlot={setSelectedSlot}
        />
      )}

      <SlotDetail
        slot={selectedSlot}
        auctions={auctions}
        agent={selectedAgent}
        onClose={() => setSelectedSlot(null)}
        onBuyNow={handleBuyNow}
        onSetOrder={handleSetOrder}
      />
    </div>
  )
}

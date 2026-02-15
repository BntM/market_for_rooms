import { useState, useEffect } from 'react'
import api from '../api'
import RoomTimeGrid from './RoomTimeGrid'
import SlotDetail from './SlotDetail'

export default function Marketplace() {
  const [resources, setResources] = useState([])
  const [auctions, setAuctions] = useState([])
  const [agents, setAgents] = useState([])
  const [selectedAgent, setSelectedAgent] = useState(null)
  const [selectedSlots, setSelectedSlots] = useState([])
  const [location, setLocation] = useState('')
  const [refreshKey, setRefreshKey] = useState(0)
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

      // Sync selectedAgent with fresh data
      if (ag.length > 0) {
        const currentId = selectedAgent?.id || localStorage.getItem('agent_id')
        const match = currentId ? ag.find((a) => a.id === currentId) : null
        setSelectedAgent(match || ag[0])
      } else {
        setSelectedAgent(null)
      }
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  // Reload when date changes
  useEffect(() => { load() }, [viewDate])

  // Listen for simulation reset
  useEffect(() => {
    const handleReset = () => { load(); setRefreshKey((k) => k + 1); setSelectedSlots([]) }
    window.addEventListener('simulation-reset', handleReset)
    return () => window.removeEventListener('simulation-reset', handleReset)
  }, [])

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

  const handleToggleSlot = (slot) => {
    setSelectedSlots((prev) => {
      const exists = prev.find((s) => s.id === slot.id)
      if (exists) return prev.filter((s) => s.id !== slot.id)
      return [...prev, slot]
    })
  }

  const handleBuyAll = async (slotsToBuy) => {
    if (!selectedAgent) return
    const items = slotsToBuy.map((slot) => {
      const auction = auctions.find((a) => a.time_slot_id === slot.id)
      return { slot, auction }
    }).filter((item) => item.auction && item.auction.status === 'active')

    if (items.length === 0) {
      alert('No active auctions for selected slots.')
      return
    }

    const total = items.reduce((sum, item) => sum + item.auction.current_price, 0)
    const confirmed = confirm(
      `Buy ${items.length} slot(s) for ${total.toFixed(1)} total tokens?\n\n` +
      items.map((item) => `  • ${item.auction.current_price.toFixed(1)} tokens`).join('\n')
    )
    if (!confirmed) return

    for (const item of items) {
      try {
        await api.placeBid(item.auction.id, {
          agent_id: selectedAgent.id,
          amount: item.auction.current_price,
        })
      } catch (e) {
        alert(`Failed to buy slot: ${e.message}`)
      }
    }
    await load()
    setRefreshKey((k) => k + 1)
    setSelectedSlots([])
  }

  const handleSetOrder = async (auction, maxPrice) => {
    if (!selectedAgent) return
    try {
      await api.createLimitOrder(auction.id, {
        agent_id: selectedAgent.id,
        max_price: maxPrice,
      })
      alert('Limit order placed')
      setRefreshKey((k) => k + 1)
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
            <input
              type="date"
              style={{ padding: '0.4rem', border: '1px solid #ddd', borderRadius: '4px' }}
              value={viewDate.toISOString().split('T')[0]}
              onChange={(e) => {
                const date = new Date(e.target.value)
                const userTimezoneOffset = date.getTimezoneOffset() * 60000;
                const adjustedDate = new Date(date.getTime() + userTimezoneOffset);
                setViewDate(adjustedDate)
              }}
            />
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
          <label>Acting as</label>
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
            {agents.length === 0 && <option value="">No agents available</option>}
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
          key={refreshKey}
          resources={filtered}
          auctions={auctions}
          selectedSlots={selectedSlots}
          onToggleSlot={handleToggleSlot}
        />
      )}

      <SlotDetail
        slots={selectedSlots}
        auctions={auctions}
        agent={selectedAgent}
        onClose={() => setSelectedSlots([])}
        onRemoveSlot={(slot) => setSelectedSlots((prev) => prev.filter((s) => s.id !== slot.id))}
        onBuyAll={handleBuyAll}
        onSetOrder={handleSetOrder}
      />
    </div>
  )
}

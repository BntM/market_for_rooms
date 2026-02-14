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

  const load = async () => {
    try {
      const [res, auc, ag] = await Promise.all([
        api.getResources(),
        api.getAuctions(),
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

  useEffect(() => { load() }, [])

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

  if (loading) return <div className="text-secondary">Loading marketplace...</div>

  return (
    <div>
      <div className="page-header">
        <h1>Marketplace</h1>
        <p>Browse available rooms and place bids on time slots</p>
      </div>

      <div className="filters-row">
        <div className="form-group">
          <label>Location</label>
          <select value={location} onChange={(e) => setLocation(e.target.value)}>
            <option value="">All locations</option>
            {locations.map((l) => (
              <option key={l} value={l}>{l}</option>
            ))}
          </select>
        </div>
        <div className="form-group">
          <label>Acting as</label>
          <select
            value={selectedAgent?.id || ''}
            onChange={(e) => {
              const a = agents.find((a) => a.id === e.target.value)
              if (a) setSelectedAgent(a)
            }}
          >
            {agents.map((a) => (
              <option key={a.id} value={a.id}>{a.name} ({a.token_balance.toFixed(1)} tokens)</option>
            ))}
          </select>
        </div>
      </div>

      {filtered.length === 0 ? (
        <div className="card text-secondary" style={{ padding: '3rem', textAlign: 'center' }}>
          No rooms available. An admin needs to create rooms and start auctions.
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

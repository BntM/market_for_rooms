import { useState, useEffect, useMemo } from 'react'
import api from '../api'
import RoomTimeGrid from '../user/RoomTimeGrid'
import SlotDetail from '../user/SlotDetail'
import { NavLink } from 'react-router-dom'
import AdminMarketAnalysis from './AdminMarketAnalysis'

// Reusing the config component logic here
const ConfigSection = () => {
  const [config, setConfig] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [show, setShow] = useState(false)

  useEffect(() => {
    if (show && !config) {
      api.getConfig()
        .then(setConfig)
        .catch(() => {
          setConfig({
            token_starting_amount: 100,
            token_frequency_days: 7,
            token_inflation_rate: 0,
            max_bookings_per_agent: 10,
            dutch_start_price: 100,
            dutch_min_price: 10,
            dutch_price_step: 5,
            dutch_tick_interval_sec: 10,
            global_price_modifier: 1.0,
          })
        })
        .finally(() => setLoading(false))
    }
  }, [show])

  const handleSave = async () => {
    setSaving(true)
    try {
      const updated = await api.updateConfig(config)
      setConfig(updated)
      alert('Configuration saved')
    } catch (e) {
      alert(e.message)
    } finally {
      setSaving(false)
    }
  }

  const field = (label, key, type = 'number', step = undefined) => (
    <div style={{ marginBottom: '1rem' }}>
      <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 500, fontSize: '0.8rem' }}>{label}</label>
      <input
        type={type}
        step={step}
        style={{ width: '100%', padding: '0.4rem', border: '1px solid #ddd', borderRadius: '4px' }}
        value={config?.[key] ?? ''}
        onChange={(e) => setConfig({ ...config, [key]: type === 'number' ? parseFloat(e.target.value) || 0 : e.target.value })}
      />
    </div>
  )

  return (
    <div className="card mb-2">
      <div className="flex-between" style={{ cursor: 'pointer' }} onClick={() => setShow(!show)}>
        <h3 style={{ margin: 0 }}>System Configuration</h3>
        <button className="btn btn--small">{show ? 'Hide' : 'Show'}</button>
      </div>
      {show && (
        <div style={{ marginTop: '1.5rem' }}>
          {loading ? <div>Loading...</div> : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1.5rem' }}>
              <div style={{ background: '#f8f9fa', padding: '1rem', borderRadius: '8px' }}>
                <h4 style={{ marginBottom: '1rem', marginTop: 0 }}>Token Economics</h4>
                {field('Starting Balance', 'token_starting_amount', 'number')}
                {field('Distribution (Days)', 'token_frequency_days', 'number', '0.1')}
                {field('Inflation Rate', 'token_inflation_rate', 'number', '0.01')}
                {field('Max Bookings', 'max_bookings_per_agent', 'number')}
              </div>
              <div style={{ background: '#f8f9fa', padding: '1rem', borderRadius: '8px' }}>
                <h4 style={{ marginBottom: '1rem', marginTop: 0 }}>Pricing Settings</h4>
                {field('Start Price', 'dutch_start_price', 'number')}
                {field('Min Price', 'dutch_min_price', 'number')}
                {field('Price Step', 'dutch_price_step', 'number')}
                {field('Global Modifier', 'global_price_modifier', 'number', '0.1')}
              </div>
              <div style={{ gridColumn: '1 / -1', textAlign: 'right' }}>
                <button className="btn btn--primary" onClick={handleSave} disabled={saving}>
                  {saving ? 'Saving...' : 'Save Configuration'}
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

const SimulationSection = () => {
  const [agents, setAgents] = useState([])
  const [loading, setLoading] = useState(true)
  const [show, setShow] = useState(false)
  const [simulating, setSimulating] = useState(false)
  const [weeks, setWeeks] = useState(1)

  const fetchAgents = async () => {
    try {
      const res = await api.getAgents()
      setAgents(res.filter(a => a.is_simulated))
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  useEffect(() => { if (show) fetchAgents() }, [show])

  const handleCreateAgent = async () => {
    try {
      await api.createAgent({
        name: `SimAgent_${agents.length + 1}`,
        is_simulated: true,
        token_balance: 100,
        behavior_risk_tolerance: 0.5,
        behavior_price_sensitivity: 0.5,
        behavior_flexibility: 0.5,
        behavior_preferred_days: "0,1,2,3,4",
        behavior_preferred_period: "any"
      })
      fetchAgents()
    } catch (e) { alert(e.message) }
  }

  const handleSimulate = async () => {
    setSimulating(true)
    try {
      const res = await api.request('/simulation/simulate-semester?weeks=' + weeks, { method: 'POST' })
      alert(`Simulation complete! Made ${res.bookings_made} bookings over ${res.days_simulated} days.`)
      window.dispatchEvent(new CustomEvent('simulation-reset', { detail: { date: res.current_date } }))
    } catch (e) { alert(e.message) }
    finally { setSimulating(false) }
  }

  const updateAgentBehavior = async (agent, updates) => {
    try {
      await api.updateAgent(agent.id, { ...agent, ...updates })
      fetchAgents()
    } catch (e) { alert(e.message) }
  }

  return (
    <div className="card mb-2">
      <div className="flex-between" style={{ cursor: 'pointer' }} onClick={() => setShow(!show)}>
        <h3 style={{ margin: 0 }}>Simulation Management</h3>
        <button className="btn btn--small">{show ? 'Hide' : 'Show'}</button>
      </div>

      {show && (
        <div style={{ marginTop: '1.5rem' }}>
          <div style={{ background: '#eef2ff', padding: '1rem', borderRadius: '8px', marginBottom: '1.5rem', display: 'flex', gap: '1rem', alignItems: 'center' }}>
            <div style={{ flex: 1 }}>
              <label style={{ display: 'block', fontWeight: 600, fontSize: '0.8rem' }}>Simulation Duration</label>
              <select value={weeks} onChange={e => setWeeks(parseInt(e.target.value))} style={{ padding: '0.4rem', borderRadius: '4px', width: '100%', border: '1px solid #ddd' }}>
                <option value={1}>1 Week</option>
                <option value={4}>1 Month (4 Weeks)</option>
                <option value={15}>Full Semester (15 Weeks)</option>
              </select>
            </div>
            <button className="btn btn--primary" onClick={handleSimulate} disabled={simulating}>
              {simulating ? 'Simulating...' : `Run Simulation`}
            </button>
          </div>

          <div className="flex-between" style={{ marginBottom: '1rem' }}>
            <h4 style={{ margin: 0 }}>Simulated Agents ({agents.length})</h4>
            <button className="btn btn--small" onClick={handleCreateAgent}>+ Create Agent</button>
          </div>

          {loading ? <div>Loading agents...</div> : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '1rem' }}>
              {agents.map(agent => (
                <div key={agent.id} style={{ background: '#fff', border: '1px solid #ddd', padding: '1rem', borderRadius: '8px', fontSize: '0.85rem' }}>
                  <div style={{ fontWeight: 'bold', marginBottom: '0.8rem', borderBottom: '1px solid #eee', paddingBottom: '0.4rem' }}>{agent.name}</div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.8rem' }}>
                    <div>
                      <label style={{ fontSize: '0.7rem', color: '#666' }}>Risk Tolerance</label>
                      <input type="number" step="0.1" value={agent.behavior_risk_tolerance} style={{ width: '100%' }}
                        onChange={(e) => updateAgentBehavior(agent, { behavior_risk_tolerance: parseFloat(e.target.value) })} />
                    </div>
                    <div>
                      <label style={{ fontSize: '0.7rem', color: '#666' }}>Price Sensitivity</label>
                      <input type="number" step="0.1" value={agent.behavior_price_sensitivity} style={{ width: '100%' }}
                        onChange={(e) => updateAgentBehavior(agent, { behavior_price_sensitivity: parseFloat(e.target.value) })} />
                    </div>
                    <div>
                      <label style={{ fontSize: '0.7rem', color: '#666' }}>Flexibility</label>
                      <input type="number" step="0.1" value={agent.behavior_flexibility} style={{ width: '100%' }}
                        onChange={(e) => updateAgentBehavior(agent, { behavior_flexibility: parseFloat(e.target.value) })} />
                    </div>
                    <div>
                      <label style={{ fontSize: '0.7rem', color: '#666' }}>Preferred Days (0-4)</label>
                      <input type="text" value={agent.behavior_preferred_days} style={{ width: '100%' }}
                        onChange={(e) => updateAgentBehavior(agent, { behavior_preferred_days: e.target.value })} />
                    </div>
                  </div>
                </div>
              ))}
              {agents.length === 0 && <div className="text-secondary">No simulated agents. Create some to run a semester simulation.</div>}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default function AdminDashboard() {
  const [resources, setResources] = useState([])
  const [auctions, setAuctions] = useState([])
  const [agents, setAgents] = useState([])
  const [selectedAgent, setSelectedAgent] = useState(null)
  const [selectedSlot, setSelectedSlot] = useState(null)
  const [selectedSlots, setSelectedSlots] = useState([])
  const [location, setLocation] = useState('')
  const [loading, setLoading] = useState(true)
  const [viewDate, setViewDate] = useState(null)
  const [simDate, setSimDate] = useState(null)
  const [error, setError] = useState(null)
  const [refreshKey, setRefreshKey] = useState(0)

  // Initialize viewDate from simulation time
  useEffect(() => {
    api.getConfig().then(c => {
      if (c?.current_simulation_date) {
        const d = new Date(c.current_simulation_date)
        setViewDate(d)
        setSimDate(d)
      } else {
        setViewDate(new Date())
        setSimDate(new Date())
      }
    }).catch(() => {
      setViewDate(new Date())
      setSimDate(new Date())
    })
  }, [])

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      const start = new Date(viewDate)
      start.setHours(0, 0, 0, 0)
      const end = new Date(viewDate)
      end.setHours(23, 59, 59, 999)

      const [res, auc, ag] = await Promise.all([
        api.getResources(),
        api.getAuctions({ start_date: start.toISOString(), end_date: end.toISOString() }),
        api.getAgents(),
      ])
      setResources(res || [])
      setAuctions(auc || [])
      setAgents(ag || [])

      if (ag && ag.length > 0 && !selectedAgent) {
        setSelectedAgent(ag[0])
      }
    } catch (e) {
      console.error(e)
      setError("Failed to load schedule data.")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { if (viewDate) load() }, [viewDate])

  // Listen for simulation reset to refresh chart and sync simDate
  useEffect(() => {
    const handleRefresh = (e) => {
      if (e.detail?.date) {
        const d = new Date(e.detail.date)
        setSimDate(d)
        setViewDate(d)
      }
      load()
    }
    window.addEventListener('simulation-reset', handleRefresh)
    return () => window.removeEventListener('simulation-reset', handleRefresh)
  }, [])

  // Add Global Reset and Allocate Buttons here too
  const handleRound = async () => { try { await api.runRound(); await load() } catch (e) { alert(e.message) } }
  const handleAllocate = async () => { try { await api.allocateTokens(); alert('Tokens Allocated') } catch (e) { alert(e.message) } }
  const handleReset = async () => {
    if (!confirm('Reset simulation?')) return;
    try { await api.resetSimulation(); window.dispatchEvent(new Event('simulation-reset')); await load() } catch (e) { alert(e.message) }
  }

  const handleToggleSlot = (slot) => {
    setSelectedSlots((prev) => {
      const exists = prev.find((s) => s.id === slot.id)
      if (exists) return prev.filter((s) => s.id !== slot.id)
      return [...prev, slot]
    })
  }

  const handleBuyAll = async (slotsToBuy, splitOptions = null) => {
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
          split_with_agent_id: splitOptions?.splitWith || null,
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

  const handleDateChange = (days) => {
    const next = new Date(viewDate)
    next.setDate(next.getDate() + days)
    setViewDate(next)
  }

  const handleDateSelect = (e) => {
    const date = new Date(e.target.value)
    // Adjust for timezone offset to keep the selected day
    const userTimezoneOffset = date.getTimezoneOffset() * 60000;
    const adjustedDate = new Date(date.getTime() + userTimezoneOffset);
    setViewDate(adjustedDate)
  }

  const locations = [...new Set((resources || []).map((r) => r.location).filter(Boolean))]
  const filtered = location
    ? (resources || []).filter((r) => r.location === location)
    : (resources || [])

  if (!viewDate) {
    return (
      <div>
        <div className="page-header">
          <h1>Admin Dashboard</h1>
          <p>Monitor schedule, configure settings, and control simulation.</p>
        </div>
        <div className="text-secondary" style={{ padding: '2rem' }}>Loading...</div>
      </div>
    )
  }

  return (
    <div>
      <div className="page-header">
        <h1>Admin Dashboard</h1>
        <p>Monitor schedule, configure settings, and control simulation.</p>
      </div>

      <ConfigSection />
      <div className="mb-4">
        <AdminMarketAnalysis />
      </div>
      <SimulationSection />

      <div className="card mb-2">
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <button className="btn btn--primary" disabled={loading} onClick={async () => {
            setLoading(true)
            try {
              const res = await api.advanceDay();
              if (res && res.current_date) {
                const d = new Date(res.current_date);
                setViewDate(d);
                setSimDate(d);
                window.dispatchEvent(new CustomEvent('simulation-reset', { detail: { date: res.current_date } }));
              } else {
                window.dispatchEvent(new Event('simulation-reset'));
              }
              await load();
            } catch (e) { alert(e.message) } finally { setLoading(false) }
          }}>
            {loading ? 'Processing...' : 'Progress a Day'}
          </button>

          <button className="btn" disabled={loading} onClick={async () => {
            setLoading(true)
            try {
              const res = await api.advanceHour();
              if (res && res.current_date) {
                const d = new Date(res.current_date);
                setViewDate(d);
                setSimDate(d);
                window.dispatchEvent(new CustomEvent('simulation-reset', { detail: { date: res.current_date } }));
              } else {
                window.dispatchEvent(new Event('simulation-reset'));
              }
              await load();
            } catch (e) { alert(e.message) } finally { setLoading(false) }
          }}>
            {loading ? '...' : 'Progress Hour'}
          </button>

          <div style={{ flex: 1 }}></div>

          <button className="btn btn--danger" onClick={async () => {
            if (!confirm('Reset simulation to Feb 14?')) return;
            try {
              await api.resetTime();
              await api.resetSimulation();
              const d = new Date("2026-02-15T09:00:00");
              setViewDate(d);
              setSimDate(d);
              window.dispatchEvent(new Event('simulation-reset'));
              await load();
            } catch (e) { alert(e.message) }
          }}>
            Reset
          </button>
        </div>
      </div>

      {error && <div className="card error">{error}</div>}

      <div className="filters-row" style={{ alignItems: 'flex-end', marginTop: '2rem' }}>
        <div className="form-group">
          <label>Date</label>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <button className="btn btn--small" onClick={() => handleDateChange(-1)}>&lt;</button>
            <input
              type="date"
              style={{ padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }}
              value={viewDate.toISOString().split('T')[0]}
              onChange={handleDateSelect}
            />
            <button className="btn btn--small" onClick={() => handleDateChange(1)}>&gt;</button>
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

        <div className="form-group">
          <label>Acting as</label>
          <select
            value={selectedAgent?.id || ''}
            onChange={(e) => {
              const a = agents.find(ag => ag.id === e.target.value)
              if (a) setSelectedAgent(a)
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
          No rooms found.
        </div>
      ) : (
        <RoomTimeGrid
          key={refreshKey}
          resources={filtered}
          auctions={auctions}
          selectedSlots={selectedSlots}
          onToggleSlot={handleToggleSlot}
          simDate={simDate}
          currentAgentId={selectedAgent?.id}
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
        agents={agents}
      />
    </div>
  )
}

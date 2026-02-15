import { useState, useEffect } from 'react'
import api from '../api'
import RoomTimeGrid from '../user/RoomTimeGrid'
import SlotDetail from '../user/SlotDetail'

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
            // Defaults
            dutch_start_price: 100,
            dutch_min_price: 10,
            dutch_price_step: 5,
            dutch_tick_interval_sec: 10,
            location_popularity: {},
            time_popularity: {},
            global_price_modifier: 1.0,
            lead_time_sensitivity: 1.0,
            capacity_weight: 1.0,
            location_weight: 1.0,
            time_of_day_weight: 1.0,
            day_of_week_weight: 1.0,
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
      <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>{label}</label>
      <input
        type={type}
        step={step}
        style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }}
        value={config?.[key] ?? ''}
        onChange={(e) => setConfig({ ...config, [key]: type === 'number' ? parseFloat(e.target.value) || 0 : e.target.value })}
      />
    </div>
  )

  return (
    <div className="card mb-2">
      <div className="flex-between" style={{ cursor: 'pointer' }} onClick={() => setShow(!show)}>
        <h3 style={{ margin: 0 }}>Settings & Configuration</h3>
        <button className="btn btn--small">{show ? 'Hide' : 'Show'}</button>
      </div>

      {show && (
        <div style={{ marginTop: '1.5rem' }}>
          {loading ? <div>Loading...</div> : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>
              <div style={{ background: '#f8f9fa', padding: '1rem', borderRadius: '8px' }}>
                <h4 style={{ marginBottom: '1rem' }}>Token Economics</h4>
                {field('Starting Token Amount', 'token_starting_amount', 'number')}
                {field('Distribution Frequency (Days)', 'token_frequency_days', 'number', '0.1')}
                {field('Inflation Rate (0.05 = 5%)', 'token_inflation_rate', 'number', '0.01')}
                {field('Max Bookings per Agent', 'max_bookings_per_agent', 'number')}
              </div>
              <div style={{ background: '#f8f9fa', padding: '1rem', borderRadius: '8px' }}>
                <h4 style={{ marginBottom: '1rem' }}>Pricing Sensitivities</h4>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                  <div>
                    {field('Global Modifier', 'global_price_modifier', 'number', '0.1')}
                    {field('Lead Time', 'lead_time_sensitivity', 'number', '0.1')}
                    {field('Capacity Weight', 'capacity_weight', 'number', '0.1')}
                  </div>
                  <div>
                    {field('Location Weight', 'location_weight', 'number', '0.1')}
                    {field('Time Weight', 'time_of_day_weight', 'number', '0.1')}
                    {field('Day Weight', 'day_of_week_weight', 'number', '0.1')}
                  </div>
                </div>
              </div>
              <div style={{ gridColumn: '1 / -1', textAlign: 'right' }}>
                <button className="btn btn--primary" onClick={(e) => { e.stopPropagation(); handleSave() }} disabled={saving}>
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

export default function AdminDashboard() {
  const [resources, setResources] = useState([])
  const [auctions, setAuctions] = useState([])
  const [selectedSlot, setSelectedSlot] = useState(null)
  const [location, setLocation] = useState('')
  const [loading, setLoading] = useState(true)
  const [viewDate, setViewDate] = useState(new Date())
  const [error, setError] = useState(null)

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      const start = new Date(viewDate)
      start.setHours(0, 0, 0, 0)
      const end = new Date(viewDate)
      end.setHours(23, 59, 59, 999)

      const [res, auc] = await Promise.all([
        api.getResources(),
        api.getAuctions({ start_date: start.toISOString(), end_date: end.toISOString() }),
      ])
      setResources(res || [])
      setAuctions(auc || [])
    } catch (e) {
      console.error(e)
      setError("Failed to load schedule data.")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [viewDate])

  // Listen for simulation reset to refresh chart
  useEffect(() => {
    const handleRefresh = () => load()
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

  return (
    <div>
      <div className="page-header">
        <h1>Admin Dashboard</h1>
        <p>Monitor schedule, configure settings, and control simulation.</p>
      </div>

      <ConfigSection />

      <div className="card mb-2">
        <div className="flex gap-2">
          <button className="btn btn--primary" onClick={handleRound}>Run Round</button>
          <button className="btn" onClick={handleAllocate}>Allocate Tokens</button>
          <button className="btn btn--danger" onClick={handleReset}>Reset All</button>
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
      </div>

      {loading ? (
        <div className="text-secondary" style={{ padding: '2rem' }}>Loading schedule...</div>
      ) : filtered.length === 0 ? (
        <div className="card text-secondary" style={{ padding: '3rem', textAlign: 'center' }}>
          No rooms found.
        </div>
      ) : (
        <RoomTimeGrid
          resources={filtered}
          auctions={auctions}
          selectedSlots={selectedSlot ? [selectedSlot] : []}
          onToggleSlot={(slot) => setSelectedSlot((prev) => prev && prev.id === slot.id ? null : slot)}
        />
      )}

      <SlotDetail
        slots={selectedSlot ? [selectedSlot] : []}
        auctions={auctions}
        agent={null}
        onClose={() => setSelectedSlot(null)}
        onRemoveSlot={() => setSelectedSlot(null)}
        onBuyAll={() => { }}
        onSetOrder={() => { }}
      />
    </div>
  )
}

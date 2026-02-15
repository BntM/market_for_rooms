import { useState, useEffect } from 'react'
import api from '../api'

export default function AuctionConfig() {
  const [config, setConfig] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    api.getConfig()
      .then(setConfig)
      .catch(() => {
        // Config might not exist yet, use defaults
        setConfig({
          token_allocation_amount: 100,
          token_allocation_frequency_hours: 24,
          max_bookings_per_agent: 10,
          dutch_start_price: 100,
          dutch_min_price: 10,
          dutch_price_step: 5,
          dutch_tick_interval_sec: 10,
          location_popularity: {},
          time_popularity: {},
        })
      })
      .finally(() => setLoading(false))
  }, [])

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

  if (loading || !config) return <div className="text-secondary">Loading config...</div>

  const field = (label, key, type = 'number', step = undefined) => (
    <div className="form-group">
      <label>{label}</label>
      <input
        type={type}
        step={step}
        value={config[key] ?? ''}
        onChange={(e) => setConfig({ ...config, [key]: type === 'number' ? parseFloat(e.target.value) || 0 : e.target.value })}
      />
    </div>
  )

  return (
    <div>
      <div className="page-header">
        <h1>Configuration</h1>
        <p>Token allocation, auction parameters, and popularity weights</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
        <div className="card">
          <h3 style={{ marginBottom: '1rem' }}>Token Allocation</h3>
          {field('Allocation Amount', 'token_allocation_amount')}
          {field('Frequency (hours)', 'token_allocation_frequency_hours', 'number', '0.5')}
          {field('Max Bookings per Agent', 'max_bookings_per_agent')}
        </div>

        <div className="card">
          <h3 style={{ marginBottom: '1rem' }}>Dutch Auction Parameters</h3>
          {field('Start Price', 'dutch_start_price')}
          {field('Min Price', 'dutch_min_price')}
          {field('Price Step', 'dutch_price_step', 'number', '0.5')}
          {field('Tick Interval (sec)', 'dutch_tick_interval_sec', 'number', '1')}
        </div>

        <div className="card">
          <h3 style={{ marginBottom: '1rem' }}>Location Popularity</h3>
          <div className="form-group">
            <label>Weights (JSON)</label>
            <textarea
              rows={6}
              value={JSON.stringify(config.location_popularity || {}, null, 2)}
              onChange={(e) => {
                try {
                  setConfig({ ...config, location_popularity: JSON.parse(e.target.value) })
                } catch { }
              }}
              style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}
            />
          </div>
        </div>

        <div className="card">
          <h3 style={{ marginBottom: '1rem' }}>Time Popularity</h3>
          <div className="form-group">
            <label>Weights (JSON)</label>
            <textarea
              rows={6}
              value={JSON.stringify(config.time_popularity || {}, null, 2)}
              onChange={(e) => {
                try {
                  setConfig({ ...config, time_popularity: JSON.parse(e.target.value) })
                } catch { }
              }}
              style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}
            />
          </div>
        </div>
        <div className="card">
          <h3 style={{ marginBottom: '1rem' }}>Pricing Sensitivities</h3>
          <p className="text-secondary small mb-1">Adjust how much each factor impacts the base price.</p>
          {field('Capacity Weight', 'capacity_weight', 'number', '0.1')}
          {field('Location Weight', 'location_weight', 'number', '0.1')}
          {field('Time Weight', 'time_weight', 'number', '0.1')}
          {field('Global Modifier', 'global_price_modifier', 'number', '0.1')}
        </div>
      </div>

      <div className="mt-2">
        <button className="btn btn--primary" onClick={handleSave} disabled={saving}>
          {saving ? 'Saving...' : 'Save Configuration'}
        </button>
      </div>
    </div>
  )
}

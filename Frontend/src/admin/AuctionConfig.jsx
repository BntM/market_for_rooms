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
          token_starting_amount: 100,
          token_frequency_days: 7,
          token_inflation_rate: 0,
          max_bookings_per_agent: 10,
          // Defaults for hidden fields
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
    <div style={{ marginBottom: '1rem' }}>
      <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>{label}</label>
      <input
        type={type}
        step={step}
        style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }}
        value={config[key] ?? ''}
        onChange={(e) => setConfig({ ...config, [key]: type === 'number' ? parseFloat(e.target.value) || 0 : e.target.value })}
      />
    </div>
  )

  return (
    <div>
      <div className="page-header" style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 700 }}>Configuration</h1>
        <p style={{ color: '#666' }}>Adjust market parameters and pricing logic.</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>

        {/* Token Economics */}
        <div className="card" style={{ background: 'white', padding: '1.5rem', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
          <h3 style={{ marginBottom: '1rem', borderBottom: '1px solid #eee', paddingBottom: '0.5rem' }}>Token Economics</h3>
          {field('Starting Token Amount', 'token_starting_amount', 'number')}
          {field('Distribution Frequency (Days)', 'token_frequency_days', 'number', '0.1')}
          {field('Inflation Rate (0.05 = 5%)', 'token_inflation_rate', 'number', '0.01')}
          {field('Max Bookings per Agent', 'max_bookings_per_agent', 'number')}
        </div>

        {/* Pricing Sensitivities */}
        <div className="card" style={{ background: 'white', padding: '1.5rem', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
          <h3 style={{ marginBottom: '1rem', borderBottom: '1px solid #eee', paddingBottom: '0.5rem' }}>Pricing Sensitivities</h3>
          <p style={{ fontSize: '0.85rem', color: '#666', marginBottom: '1rem' }}>Adjust the multiplier weights for each pricing factor.</p>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div>
              {field('Global Modifier', 'global_price_modifier', 'number', '0.1')}
              {field('Lead Time (Curve)', 'lead_time_sensitivity', 'number', '0.1')}
              {field('Capacity Weight', 'capacity_weight', 'number', '0.1')}
            </div>
            <div>
              {field('Location Weight', 'location_weight', 'number', '0.1')}
              {field('Time of Day Weight', 'time_of_day_weight', 'number', '0.1')}
              {field('Day of Week Weight', 'day_of_week_weight', 'number', '0.1')}
            </div>
          </div>
        </div>
      </div>

      <div style={{ marginTop: '2rem', textAlign: 'right' }}>
        <button
          onClick={handleSave}
          disabled={saving}
          style={{
            padding: '0.75rem 1.5rem',
            background: '#2563eb', // Blue
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: saving ? 'not-allowed' : 'pointer',
            opacity: saving ? 0.7 : 1,
            fontWeight: 500
          }}
        >
          {saving ? 'Saving...' : 'Save Configuration'}
        </button>
      </div>
    </div>
  )
}

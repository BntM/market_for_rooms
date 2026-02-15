import { useState, useEffect } from 'react'
import api from '../api'

export default function Initialization() {
    const [resetting, setResetting] = useState(false)
    const [message, setMessage] = useState(null)

    const [config, setConfig] = useState({
        global_price_modifier: 1.0,
        lead_time_sensitivity: 1.0,
        capacity_weight: 1.0,
        location_weight: 1.0,
        time_of_day_weight: 1.0,
        day_of_week_weight: 1.0,
    })

    useEffect(() => {
        api.getConfig().then(data => {
            if (data) {
                setConfig({
                    global_price_modifier: data.global_price_modifier ?? 1.0,
                    lead_time_sensitivity: data.lead_time_sensitivity ?? 1.0,
                    capacity_weight: data.capacity_weight ?? 1.0,
                    location_weight: data.location_weight ?? 1.0,
                    time_of_day_weight: data.time_of_day_weight ?? 1.0,
                    day_of_week_weight: data.day_of_week_weight ?? 1.0,
                })
            }
        })
    }, [])

    const handleResetDefaults = async () => {
        if (!confirm("This will DELETE ALL active auctions/slots and reload the default GMU dataset. Are you sure?")) return

        setResetting(true)
        setMessage(null)
        try {
            await api.updateConfig(config)
            const res = await api.resetAndLoadDefaults()
            setMessage(`Success! Created ${res.resources_created} resources and ${res.time_slots_created} slots.`)
        } catch (e) {
            setMessage(`Error: ${e.message}`)
        } finally {
            setResetting(false)
        }
    }

    const handleUpdateWeights = async () => {
        try {
            await api.updateConfig(config)
            setMessage("Settings saved. Run 'Reset & Load' to apply to new data import.")
        } catch (e) {
            setMessage("Error saving settings")
        }
    }

    const slider = (label, key, min = 0, max = 5, step = 0.1) => (
        <div style={{ marginBottom: '1.25rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
                <label style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: '0.75rem',
                    fontWeight: 500,
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                    color: 'var(--color-text-secondary)',
                }}>{label}</label>
                <span style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: '0.85rem',
                    fontWeight: 500,
                    background: 'var(--color-highlight)',
                    padding: '0 0.4rem',
                    border: '1px solid var(--color-border)',
                }}>{config[key].toFixed(1)}</span>
            </div>
            <input
                type="range"
                min={min}
                max={max}
                step={step}
                className="themed-slider"
                value={config[key]}
                onChange={(e) => setConfig({ ...config, [key]: parseFloat(e.target.value) })}
            />
        </div>
    )

    return (
        <div>
            <div className="page-header">
                <h1>Initialization & Pricing</h1>
                <p>Load default data and tune initial pricing logic</p>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>

                <div className="card">
                    <h3 style={{ marginBottom: '0.5rem' }}>Pricing Factors</h3>
                    <p className="text-secondary" style={{ fontSize: '0.85rem', marginBottom: '1.5rem', fontFamily: 'var(--font-heading)', fontStyle: 'italic' }}>
                        Higher values increase that factor's influence on price.
                    </p>

                    {slider("Global Price Modifier", "global_price_modifier", 0.1, 5.0)}
                    {slider("Lead Time Sensitivity", "lead_time_sensitivity")}
                    {slider("Capacity Weight", "capacity_weight")}
                    {slider("Location Weight", "location_weight")}
                    {slider("Time of Day Weight", "time_of_day_weight")}
                    {slider("Day of Week Weight", "day_of_week_weight")}

                    <div style={{ marginTop: '1.5rem', paddingTop: '1.5rem', borderTop: '1px solid var(--color-border)' }}>
                        <button className="btn" onClick={handleUpdateWeights} style={{ width: '100%' }}>
                            Save Settings Only
                        </button>
                    </div>
                </div>

                <div className="card" style={{ background: 'var(--color-bg)' }}>
                    <h3 style={{ marginBottom: '0.5rem' }}>Data Initialization</h3>
                    <p style={{ marginBottom: '1rem', fontSize: '0.875rem' }}>
                        Use the default GMU dataset (14-day history) to train the model and generate
                        future availability for the next 4 months.
                    </p>

                    <div style={{ marginBottom: '1.5rem', padding: '1rem', background: 'var(--color-surface)', border: '1px solid var(--color-border)' }}>
                        <p style={{
                            fontSize: '0.75rem',
                            fontFamily: 'var(--font-mono)',
                            fontWeight: 500,
                            textTransform: 'uppercase',
                            letterSpacing: '0.05em',
                            marginBottom: '0.5rem',
                        }}>This process will:</p>
                        <ul style={{ fontSize: '0.85rem', listStyle: 'none', paddingLeft: 0, display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                            <li style={{ paddingLeft: '1rem', borderLeft: '2px solid var(--color-accent)' }}>Delete all existing slots and auctions</li>
                            <li style={{ paddingLeft: '1rem', borderLeft: '2px solid var(--color-accent)' }}>Learn demand patterns from gmu_room_data_full.csv</li>
                            <li style={{ paddingLeft: '1rem', borderLeft: '2px solid var(--color-accent)' }}>Generate ~120 days of future slots</li>
                            <li style={{ paddingLeft: '1rem', borderLeft: '2px solid var(--color-accent)' }}>Calculate initial prices based on the sliders</li>
                        </ul>
                    </div>

                    <button
                        className="btn btn--danger"
                        onClick={handleResetDefaults}
                        disabled={resetting}
                        style={{
                            width: '100%',
                            padding: '0.75rem',
                            justifyContent: 'center',
                            opacity: resetting ? 0.6 : 1,
                            cursor: resetting ? 'not-allowed' : 'pointer',
                        }}
                    >
                        {resetting ? 'Initializing...' : 'Reset & Load Default Data'}
                    </button>

                    {message && (
                        <div style={{
                            marginTop: '1rem',
                            padding: '0.75rem',
                            border: '1px solid',
                            fontFamily: 'var(--font-mono)',
                            fontSize: '0.8rem',
                            borderColor: message.startsWith('Error') ? 'var(--color-negative)' : 'var(--color-positive)',
                            background: message.startsWith('Error') ? '#fbe8e8' : '#e8f2ec',
                            color: message.startsWith('Error') ? 'var(--color-negative)' : 'var(--color-positive)',
                        }}>
                            {message}
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}

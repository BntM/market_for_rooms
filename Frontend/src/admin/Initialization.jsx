import { useState, useEffect } from 'react'
import api from '../api'

// We will use Recharts or similar for visualization if needed, 
// for now just controls.

export default function Initialization() {
    const [loading, setLoading] = useState(false)
    const [resetting, setResetting] = useState(false)
    const [message, setMessage] = useState(null)

    // Local state for pricing manipulation before "Apply"
    const [config, setConfig] = useState({
        global_price_modifier: 1.0,
        lead_time_sensitivity: 1.0,
        capacity_weight: 1.0,
        location_weight: 1.0,
        time_of_day_weight: 1.0,
        day_of_week_weight: 1.0,
    })

    useEffect(() => {
        // Load current config
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
        if (!confirm("This will DELETE ALL active auctions/slots and reload the default GMU dataset. Are you sure?")) return;

        setResetting(true)
        setMessage(null)
        try {
            // We first save the current sensitivity settings? 
            // Or does reset use the *learned* popularity but *config* sensitivities?
            // Our backend reset_and_load_defaults just imports. It uses current config ID=1.
            // So we should probably save config first if user changed sliders here.

            await api.updateConfig(config);
            const res = await api.resetAndLoadDefaults();
            setMessage(`Success! Created ${res.resources_created} resources and ${res.time_slots_created} slots.`);
        } catch (e) {
            setMessage(`Error: ${e.message}`)
        } finally {
            setResetting(false)
        }
    }

    const handleUpdateWeights = async () => {
        // Just update config without resetting data?
        // User wants to "manipulate the initial pricing".
        // Usually this means re-calculating prices for existing slots.
        // We don't have a backend endpoint for "Recalculate Prices" yet without re-importing.
        // But for now, "Reset and Load" does everything.
        // Let's make "Apply & Reload" the primary action.
        // Or we can just save config.

        // Let's assume the user flow is: Adjust Sliders -> Reset & Load with new settings.
        // So saving config is implicit in Reset.
        try {
            await api.updateConfig(config);
            setMessage("Settings saved. Run 'Reset & Load' to apply to new data import.")
        } catch (e) {
            setMessage("Error saving settings")
        }
    }

    const slider = (label, key, min = 0, max = 5, step = 0.1) => (
        <div style={{ marginBottom: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                <label style={{ fontWeight: 500 }}>{label}</label>
                <span style={{ fontFamily: 'monospace' }}>{config[key]}</span>
            </div>
            <input
                type="range"
                min={min}
                max={max}
                step={step}
                style={{ width: '100%' }}
                value={config[key]}
                onChange={(e) => setConfig({ ...config, [key]: parseFloat(e.target.value) })}
            />
        </div>
    )

    return (
        <div className="bg-white rounded-lg shadow p-6">
            <div className="page-header" style={{ marginBottom: '2rem' }}>
                <h1 style={{ fontSize: '1.5rem', fontWeight: 700 }}>Initialization & Pricing</h1>
                <p style={{ color: '#666' }}>Load default data and tune initial pricing logic.</p>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>

                {/* Controls */}
                <div>
                    <h3 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '1rem' }}>Pricing Factors</h3>
                    <p style={{ fontSize: '0.9rem', color: '#666', marginBottom: '1.5rem' }}>
                        Adjust these weights. Higher values mean that factor has more influence on the price.
                    </p>

                    {slider("Global Price Modifier", "global_price_modifier", 0.1, 5.0)}
                    {slider("Lead Time Sensitivity", "lead_time_sensitivity")}
                    {slider("Capacity Weight", "capacity_weight")}
                    {slider("Location Weight", "location_weight")}
                    {slider("Time of Day Weight", "time_of_day_weight")}
                    {slider("Day of Week Weight", "day_of_week_weight")}

                    <div style={{ marginTop: '1rem' }}>
                        <button
                            onClick={handleUpdateWeights}
                            className="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300"
                        >
                            Save Settings Only
                        </button>
                    </div>
                </div>

                {/* Actions & Info */}
                <div style={{ background: '#f8fafc', padding: '1.5rem', borderRadius: '8px' }}>
                    <h3 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '1rem' }}>Data Initialization</h3>
                    <p style={{ marginBottom: '1rem', fontSize: '0.9rem' }}>
                        Use the default GMU dataset (14-day history) to train the model and generate
                        future availability for the next 4 months.
                    </p>

                    <div style={{ marginBottom: '2rem' }}>
                        <p style={{ fontSize: '0.85rem', fontWeight: 'bold' }}>This process will:</p>
                        <ul style={{ fontSize: '0.85rem', listStyle: 'disc', paddingLeft: '1.2rem', marginTop: '0.5rem' }}>
                            <li>Delete all existing slots and auctions.</li>
                            <li>Learn demand patterns from <code>gmu_room_data_full.csv</code>.</li>
                            <li>Generate ~120 days of future slots.</li>
                            <li>Calculate initial prices based on the sliders to the left.</li>
                        </ul>
                    </div>

                    <button
                        onClick={handleResetDefaults}
                        disabled={resetting}
                        style={{
                            width: '100%',
                            padding: '1rem',
                            background: resetting ? '#94a3b8' : '#dc2626', // Red
                            color: 'white',
                            border: 'none',
                            borderRadius: '6px',
                            fontSize: '1rem',
                            fontWeight: 600,
                            cursor: resetting ? 'not-allowed' : 'pointer'
                        }}
                    >
                        {resetting ? 'Initializing...' : 'Reset & Load Default Data'}
                    </button>

                    {message && (
                        <div style={{
                            marginTop: '1rem',
                            padding: '1rem',
                            borderRadius: '4px',
                            background: message.startsWith('Error') ? '#fee2e2' : '#dcfce7',
                            color: message.startsWith('Error') ? '#991b1b' : '#166534'
                        }}>
                            {message}
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}

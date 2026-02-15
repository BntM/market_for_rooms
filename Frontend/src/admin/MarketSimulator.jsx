import { useState } from 'react'
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    Title,
    Tooltip,
    Legend,
} from 'chart.js'
import { Line, Bar } from 'react-chartjs-2'
import api from '../api'

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    Title,
    Tooltip,
    Legend
)

export default function MarketSimulator() {
    const [loading, setLoading] = useState(false)
    const [mode, setMode] = useState('simple') // simple, advanced, optimizer

    // Base Config
    const [basePrice, setBasePrice] = useState(10)
    const [days, setDays] = useState(14)
    const [tokenDrip, setTokenDrip] = useState(5)
    const [numAgents, setNumAgents] = useState(100)
    const [useRealRooms, setUseRealRooms] = useState(true)

    // Advanced Config
    const [customAgents, setCustomAgents] = useState([
        { name: 'Average Student', count: 80, budget_mult: 1.0, urgency_min: 0.1, urgency_max: 0.5 },
        { name: 'Rich Procrastinator', count: 20, budget_mult: 2.0, urgency_min: 0.5, urgency_max: 1.0 },
    ])
    const [individualAgents, setIndividualAgents] = useState([])
    const [events, setEvents] = useState([]) // Array of { day: 7, multiplier: 2.0 }
    const [newEventDay, setNewEventDay] = useState('')
    const [newEventMult, setNewEventMult] = useState(1.5)

    // Results
    const [results, setResults] = useState(null)
    const [optResults, setOptResults] = useState(null)

    const runSimulation = async () => {
        setLoading(true)
        try {
            let agentConfigs = []
            if (mode === 'simple') {
                agentConfigs = [{ name: 'Standard Agent', count: numAgents, budget_mult: 1.0, urgency_min: 0.1, urgency_max: 0.8 }]
            } else {
                agentConfigs = [
                    ...customAgents,
                    ...individualAgents.map(a => ({
                        ...a,
                        count: 1,
                        urgency_min: parseFloat(a.urgency),
                        urgency_max: parseFloat(a.urgency)
                    }))
                ]
            }

            const eventDict = events.reduce((acc, curr) => ({ ...acc, [curr.day]: curr.multiplier }), {})

            const config = {
                days,
                base_price: basePrice,
                token_drip: tokenDrip,
                weights: {
                    location: { "Library": 1.3, "Student Center": 1.2, "Engineering Hall": 1.1 },
                    capacity: { "2": 1.0, "4": 1.4, "6": 1.8, "10": 2.5 }
                },
                agent_configs: agentConfigs,
                events: eventDict,
                use_real_rooms: useRealRooms
            }

            const res = await api.runMarketSimulation(config)
            setResults(res)
            setOptResults(null)
        } catch (e) {
            alert(e.message)
        } finally {
            setLoading(false)
        }
    }

    const runOptimization = async () => {
        setLoading(true)
        try {
            const config = {
                days,
                token_drip: tokenDrip,
                weights: { location: { "Library": 1.3 }, capacity: { "4": 1.4 } },
                agent_configs: customAgents,
                events: events.reduce((acc, curr) => ({ ...acc, [curr.day]: curr.multiplier }), {}),
                use_real_rooms: useRealRooms,
                price_range_start: 5,
                price_range_end: 50,
                price_step: 3
            }
            const res = await api.optimizePrice(config)
            setOptResults(res)
            setResults(null)
        } catch (e) {
            alert(e.message)
        } finally {
            setLoading(false)
        }
    }

    const handleAddAgent = () => {
        setCustomAgents([...customAgents, { name: 'New Agent', count: 10, budget_mult: 1.0, urgency_min: 0.1, urgency_max: 0.5 }])
    }

    const handleAddIndividualAgent = () => {
        setIndividualAgents([...individualAgents, { name: 'Indv Agent', budget_mult: 1.0, urgency: 0.5, pref_location: 'Library' }])
    }

    const handleAddEvent = () => {
        if (newEventDay) {
            setEvents([...events, { day: parseInt(newEventDay), multiplier: parseFloat(newEventMult) }])
            setNewEventDay('')
        }
    }

    // Visualization Data preparation
    const getDailyBookings = () => {
        if (!results) return null
        const dayCounts = {}
        for (let i = 0; i < days; i++) dayCounts[i] = 0
        results.forEach(r => dayCounts[r.day] = (dayCounts[r.day] || 0) + 1)

        return {
            labels: Object.keys(dayCounts),
            datasets: [{
                label: 'Bookings per Day',
                data: Object.values(dayCounts),
                backgroundColor: '#4bc0c0'
            }]
        }
    }

    const getPriceTTE = () => {
        if (!results) return null
        // Scatter plot approximation using bubbles or just mixed line
        // For chartjs line, we need sorted data. Let's do Average Price per TTE
        const tteMap = {}
        results.forEach(r => {
            if (!tteMap[r.tte]) tteMap[r.tte] = []
            tteMap[r.tte].push(r.price_paid)
        })

        const labels = Object.keys(tteMap).sort((a, b) => a - b)
        const data = labels.map(l => {
            const prices = tteMap[l]
            return prices.reduce((a, b) => a + b, 0) / prices.length
        })

        return {
            labels,
            datasets: [{
                label: 'Avg Price vs Days Until Slot (TTE)',
                data,
                borderColor: '#ff6384',
                backgroundColor: '#ff6384',
                tension: 0.4
            }]
        }
    }

    return (
        <div className="container">
            <div className="page-header">
                <h1>Market Simulator</h1>
                <div style={{ display: 'flex', gap: '1rem' }}>
                    <button className={`btn btn--${mode === 'simple' ? 'primary' : 'secondary'}`} onClick={() => setMode('simple')}>Simple</button>
                    <button className={`btn btn--${mode === 'advanced' ? 'primary' : 'secondary'}`} onClick={() => setMode('advanced')}>Advanced</button>
                    <button className={`btn btn--${mode === 'optimizer' ? 'primary' : 'secondary'}`} onClick={() => setMode('optimizer')}>Optimizer</button>
                </div>
            </div>

            <div className="card" style={{ marginBottom: '2rem' }}>
                <div className="grid">
                    <div className="form-group">
                        <label>Base Price (Tokens)</label>
                        <input type="range" min="5" max="50" value={basePrice} onChange={e => setBasePrice(parseInt(e.target.value))} />
                        <span>{basePrice}</span>
                    </div>
                    <div className="form-group">
                        <label>Sim Duration (Days)</label>
                        <input type="number" value={days} onChange={e => setDays(parseInt(e.target.value))} />
                    </div>
                    <div className="form-group">
                        <label>Daily Token Drip</label>
                        <input type="number" value={tokenDrip} onChange={e => setTokenDrip(parseFloat(e.target.value))} />
                    </div>
                </div>

                {mode === 'simple' && (
                    <div className="form-group">
                        <label>Number of Standard Agents</label>
                        <input type="number" value={numAgents} onChange={e => setNumAgents(parseInt(e.target.value))} />
                    </div>
                )}

                <div className="form-group" style={{ flexDirection: 'row', alignItems: 'center', gap: '0.5rem', marginTop: '1rem' }}>
                    <input type="checkbox" checked={useRealRooms} onChange={e => setUseRealRooms(e.target.checked)} id="useRealRooms" />
                    <label htmlFor="useRealRooms" style={{ marginBottom: 0 }}>Use Actual Market Rooms (from DB)</label>
                </div>

                {mode !== 'simple' && (
                    <div style={{ marginTop: '1rem', borderTop: '1px solid #eee', paddingTop: '1rem' }}>
                        <h3>👥 Custom Agents</h3>
                        {customAgents.map((a, i) => (
                            <div key={i} className="grid" style={{ gap: '0.5rem', marginBottom: '0.5rem' }}>
                                <input placeholder="Name" value={a.name} onChange={e => { const n = [...customAgents]; n[i].name = e.target.value; setCustomAgents(n) }} />
                                <input type="number" placeholder="Count" value={a.count} onChange={e => { const n = [...customAgents]; n[i].count = parseInt(e.target.value); setCustomAgents(n) }} />
                                <input type="number" placeholder="Budget X" step="0.1" value={a.budget_mult} onChange={e => { const n = [...customAgents]; n[i].budget_mult = parseFloat(e.target.value); setCustomAgents(n) }} />
                            </div>
                        ))}
                        <button className="btn btn--small" onClick={handleAddAgent}>+ Add Agent Type</button>

                        <h3 style={{ marginTop: '1rem' }}>👤 Individual Agents</h3>
                        {individualAgents.map((a, i) => (
                            <div key={i} className="grid" style={{ gap: '0.5rem', marginBottom: '0.5rem', gridTemplateColumns: 'repeat(5, 1fr)' }}>
                                <input placeholder="Name" value={a.name} onChange={e => { const n = [...individualAgents]; n[i].name = e.target.value; setIndividualAgents(n) }} />
                                <input type="number" placeholder="Budget X" step="0.1" value={a.budget_mult} onChange={e => { const n = [...individualAgents]; n[i].budget_mult = parseFloat(e.target.value); setIndividualAgents(n) }} />
                                <input type="number" placeholder="Urgency (0-1)" step="0.1" min="0" max="1" value={a.urgency} onChange={e => { const n = [...individualAgents]; n[i].urgency = parseFloat(e.target.value); setIndividualAgents(n) }} />
                                <select value={a.pref_location} onChange={e => { const n = [...individualAgents]; n[i].pref_location = e.target.value; setIndividualAgents(n) }}>
                                    <option value="Library">Library</option>
                                    <option value="Student Center">Student Center</option>
                                    <option value="Engineering Hall">Engineering Hall</option>
                                </select>
                                <button className="btn btn--small btn--danger" onClick={() => { const n = individualAgents.filter((_, idx) => idx !== i); setIndividualAgents(n) }}>X</button>
                            </div>
                        ))}
                        <button className="btn btn--small" onClick={handleAddIndividualAgent}>+ Add Individual Agent</button>

                        <h3 style={{ marginTop: '1rem' }}>📅 Seasonality (Events)</h3>
                        <div className="grid" style={{ alignItems: 'end' }}>
                            <div className="form-group">
                                <label>Day Index</label>
                                <input type="number" value={newEventDay} onChange={e => setNewEventDay(e.target.value)} />
                            </div>
                            <div className="form-group">
                                <label>Demand Multiplier</label>
                                <input type="number" step="0.1" value={newEventMult} onChange={e => setNewEventMult(e.target.value)} />
                            </div>
                            <button className="btn btn--small" onClick={handleAddEvent}>Add Event</button>
                        </div>
                        <ul>
                            {events.map((e, i) => <li key={i}>Day {e.day}: {e.multiplier}x Demand</li>)}
                        </ul>
                    </div>
                )}

                <div style={{ marginTop: '2rem' }}>
                    {mode === 'optimizer' ? (
                        <button className="btn btn--primary" onClick={runOptimization} disabled={loading}>{loading ? 'Optimizing...' : 'Find Best Price'}</button>
                    ) : (
                        <button className="btn btn--primary" onClick={runSimulation} disabled={loading}>{loading ? 'Simulating...' : 'Run Simulation'}</button>
                    )}
                </div>
            </div>

            {optResults && (
                <div className="card notification notification--success">
                    <h2>Optimization Complete</h2>
                    <p>Creating max revenue of <strong>{optResults.max_revenue.toFixed(0)} tokens</strong></p>
                    <h3>Recommended Base Price: {optResults.best_base_price}</h3>
                </div>
            )}

            {results && (
                <div className="grid">
                    <div className="card">
                        <h3>Booking Volume per Day</h3>
                        <Bar data={getDailyBookings()} options={{ responsive: true }} />
                    </div>
                    <div className="card">
                        <h3>Price vs TTE Curve</h3>
                        <Line data={getPriceTTE()} options={{ responsive: true }} />
                    </div>

                    <div className="card" style={{ gridColumn: '1 / -1' }}>
                        <h3>Simulation Stats</h3>
                        <div className="grid">
                            <div>Total Revenue: {results.reduce((a, b) => a + b.price_paid, 0).toFixed(0)} tokens</div>
                            <div>Total Bookings: {results.length}</div>
                            <div>Avg Price: {(results.reduce((a, b) => a + b.price_paid, 0) / results.length).toFixed(2)}</div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}

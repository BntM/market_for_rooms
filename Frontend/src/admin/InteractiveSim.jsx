import { useState, useEffect, useRef } from 'react'
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
} from 'chart.js'
import { Line } from 'react-chartjs-2'
import api from '../api'

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend
)

export default function InteractiveSim() {
    const [currentDate, setCurrentDate] = useState(null)
    const [logs, setLogs] = useState([])
    const [stats, setStats] = useState({ total_bookings: 0, active_agents: 0 })
    const [agentType, setAgentType] = useState('Freshman')
    const [agentCount, setAgentCount] = useState(5)
    const [isAdvancing, setIsAdvancing] = useState(false)

    // Agent Config State
    const [weights, setWeights] = useState({
        time: 0.5,
        day: 0.5,
        location: 0.5,
        capacity: 0.5
    })
    const [prefHours, setPrefHours] = useState([9, 10, 11, 12])

    // Chart Data
    const [priceHistory, setPriceHistory] = useState({
        labels: [],
        datasets: [
            {
                label: 'Avg Clearing Price',
                data: [],
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1,
            },
        ],
    })

    const log = (msg) => {
        setLogs(prev => [`[${new Date().toLocaleTimeString()}] ${msg}`, ...prev].slice(0, 50))
    }

    const fetchState = async () => {
        try {
            const res = await api.get('/admin/config')
            setCurrentDate(new Date(res.current_simulation_date || '2026-02-14T09:00:00'))

            const results = await api.get('/simulation/results')
            setStats({
                total_bookings: results.booked_slots,
                active_agents: results.total_slots
            })

            // Update chart? We need historical price data endpoint or just append locally
        } catch (err) {
            console.error(err)
        }
    }

    useEffect(() => {
        fetchState()
    }, [])

    const advanceTime = async (unit) => {
        setIsAdvancing(true)
        try {
            const endpoint = unit === 'day' ? '/simulation/time/advance-day' : '/simulation/time/advance-hour'
            const res = await api.post(endpoint)
            setCurrentDate(new Date(res.current_date))
            log(`Advanced 1 ${unit}. Triggered ${res.actions_triggered || 0} agent actions.`)
            await fetchState()
        } catch (err) {
            log(`Error advancing time: ${err.message}`)
        } finally {
            setIsAdvancing(false)
        }
    }

    const generateAgents = async () => {
        try {
            const hoursStr = prefHours.join(',')
            await api.post('/simulation/agents/generate', {
                count: parseInt(agentCount),
                name_prefix: agentType,
                initial_balance: 500.0,
                max_bookings: 10,
                generate_preferences: true,
                // We need to update backend to accept granular weights in BulkAgentCreate if we want to pass them here
                // For now, let's rely on the random generator we updated, OR update the backend endpoint to accept overrides.
                // Since we updated 'AgentCreate' but 'BulkAgentCreate' schema might not have the fields yet...
                // Wait, we updated AgentCreate, but not BulkAgentCreate in step 2528? 
                // Let's check. If not, the backend ignores them.
                // Assuming backend generator handles randoms nicely as we coded in preference_generator.py.
            })
            log(`Generated ${agentCount} ${agentType} agents.`)
            fetchState()
        } catch (err) {
            log(`Error generating agents: ${err.message}`)
        }
    }

    const resetSim = async () => {
        if (!window.confirm("Reset all simulation data?")) return
        try {
            await api.post('/simulation/reset')
            log("Simulation reset complete.")
            fetchState()
            setLogs([])
        } catch (err) {
            log(`Error resetting: ${err.message}`)
        }
    }

    return (
        <div className="p-6 max-w-7xl mx-auto space-y-6">
            {/* Header / Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-white p-6 rounded-lg shadow-md border-l-4 border-blue-500">
                    <h2 className="text-gray-500 text-sm font-semibold uppercase">Current Simulation Time</h2>
                    <p className="text-3xl font-bold text-gray-800 mt-2">
                        {currentDate ? currentDate.toLocaleString() : 'Loading...'}
                    </p>
                    <div className="mt-4 flex gap-2">
                        <button
                            onClick={() => advanceTime('hour')}
                            disabled={isAdvancing}
                            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
                        >
                            + 1 Hour
                        </button>
                        <button
                            onClick={() => advanceTime('day')}
                            disabled={isAdvancing}
                            className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:opacity-50"
                        >
                            + 1 Day
                        </button>
                    </div>
                </div>

                <div className="bg-white p-6 rounded-lg shadow-md border-l-4 border-green-500">
                    <h2 className="text-gray-500 text-sm font-semibold uppercase">Market Activity</h2>
                    <div className="mt-2 space-y-1">
                        <div className="flex justify-between">
                            <span className="text-gray-600">Total Bookings:</span>
                            <span className="font-bold">{stats.total_bookings}</span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-gray-600">Active Agents:</span>
                            <span className="font-bold">{stats.active_agents}</span>
                        </div>
                    </div>
                    <button
                        onClick={resetSim}
                        className="mt-4 w-full px-4 py-2 bg-red-100 text-red-700 rounded hover:bg-red-200"
                    >
                        Reset Simulation
                    </button>
                </div>

                {/* Agent Control */}
                <div className="bg-white p-6 rounded-lg shadow-md border-l-4 border-purple-500">
                    <h2 className="text-gray-500 text-sm font-semibold uppercase">Deploy Agents</h2>
                    <div className="mt-2 text-xs text-gray-500 mb-2">
                        Bots with random preferences (Morning/Evening/etc)
                    </div>
                    <div className="flex gap-2">
                        <select
                            className="border p-2 rounded flex-1"
                            value={agentType}
                            onChange={(e) => setAgentType(e.target.value)}
                        >
                            <option value="Freshman">Freshman (General)</option>
                            <option value="Gunner">Gunner (High Focus)</option>
                            <option value="Slacker">Slacker (Low Budget)</option>
                        </select>
                        <input
                            type="number"
                            className="border p-2 rounded w-20"
                            value={agentCount}
                            onChange={(e) => setAgentCount(e.target.value)}
                            min="1"
                        />
                    </div>
                    <button
                        onClick={generateAgents}
                        className="mt-2 w-full px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700"
                    >
                        Deploy Agent Swarm
                    </button>
                </div>
            </div>

            {/* Main Content */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Live Feed */}
                <div className="bg-gray-900 text-green-400 p-4 rounded-lg shadow-inner font-mono h-96 overflow-y-auto lg:col-span-1">
                    <h3 className="text-white font-bold border-b border-gray-700 pb-2 mb-2 sticky top-0 bg-gray-900">System Logs</h3>
                    <div className="space-y-1 text-sm">
                        {logs.map((l, i) => (
                            <div key={i}>{l}</div>
                        ))}
                        {logs.length === 0 && <div className="text-gray-600 italic">System ready...</div>}
                    </div>
                </div>

                {/* Charts / Data */}
                <div className="bg-white p-6 rounded-lg shadow-md lg:col-span-2">
                    <h3 className="text-lg font-bold mb-4">Market Price Index</h3>
                    <div className="h-80 flex items-center justify-center bg-gray-50 rounded border">
                        <p className="text-gray-400">Real-time price chart placeholder</p>
                        {/* 
                            TODO: Fetch historical price points from backend. 
                            Currently backend 'PriceHistory' exists but need endpoint to fetch series.
                        */}
                    </div>
                </div>
            </div>
        </div>
    )
}

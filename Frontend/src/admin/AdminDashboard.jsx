import { useState, useEffect } from 'react'
import api from '../api'
import PriceChart from '../components/PriceChart'

export default function AdminDashboard() {
  const [state, setState] = useState(null)
  const [results, setResults] = useState(null)
  const [priceHistory, setPriceHistory] = useState([])
  const [loading, setLoading] = useState(true)

  const load = async () => {
    try {
      const [s, r, ph] = await Promise.all([
        api.getMarketState(),
        api.getSimulationResults().catch(() => null),
        api.getMarketPriceHistory(200),
      ])
      setState(s)
      setResults(r)
      setPriceHistory(ph)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const handleRound = async () => {
    try {
      await api.runRound()
      await load()
    } catch (e) {
      alert(e.message)
    }
  }

  const handleAllocate = async () => {
    try {
      await api.allocateTokens()
      await load()
    } catch (e) {
      alert(e.message)
    }
  }

  const handleReset = async () => {
    if (!confirm('Reset all simulation data? This cannot be undone.')) return
    try {
      await api.resetSimulation()
      await load()
    } catch (e) {
      alert(e.message)
    }
  }

  if (loading) return <div className="text-secondary">Loading dashboard...</div>

  return (
    <div>
      <div className="page-header">
        <h1>Admin Dashboard</h1>
        <p>Market overview and simulation controls</p>
      </div>

      <div className="stats-row">
        <div className="card card--stat">
          <div className="label">Total Rooms</div>
          <div className="value">{state?.resources_count ?? '—'}</div>
        </div>
        <div className="card card--stat">
          <div className="label">Active Auctions</div>
          <div className="value">{state?.active_auctions_count ?? '—'}</div>
        </div>
        <div className="card card--stat">
          <div className="label">Total Bookings</div>
          <div className="value">{state?.bookings_count ?? '—'}</div>
        </div>
        <div className="card card--stat">
          <div className="label">Avg Clearing Price</div>
          <div className="value">
            {results?.average_clearing_price != null
              ? results.average_clearing_price.toFixed(1)
              : '—'}
          </div>
        </div>
      </div>

      <div className="flex gap-2 mb-2">
        <button className="btn btn--primary" onClick={handleRound}>Run Simulation Round</button>
        <button className="btn" onClick={handleAllocate}>Allocate Tokens</button>
        <button className="btn btn--danger" onClick={handleReset}>Reset Simulation</button>
      </div>

      <div className="card mt-2">
        <h3 style={{ marginBottom: '1rem' }}>Price History</h3>
        <PriceChart data={priceHistory} height={300} />
      </div>
    </div>
  )
}

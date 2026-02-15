import { useState, useEffect } from 'react'
import api from '../api'

export default function MyBookings() {
  const [agents, setAgents] = useState([])
  const [selectedAgent, setSelectedAgent] = useState(null)
  const [bookings, setBookings] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getAgents().then((data) => {
      setAgents(data)
      const stored = localStorage.getItem('agent_id')
      const match = stored ? data.find((a) => a.id === stored) : null
      if (match) setSelectedAgent(match)
      else if (data.length > 0) setSelectedAgent(data[0])
    }).catch(() => {}).finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    if (selectedAgent) {
      api.getAgentBookings(selectedAgent.id).then(setBookings).catch(() => setBookings([]))
    }
  }, [selectedAgent?.id])

  const formatDateTime = (isoStr) => {
    if (!isoStr) return '—'
    const d = new Date(isoStr)
    return d.toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
  }

  if (loading) return <div className="text-secondary">Loading...</div>

  return (
    <div>
      <div className="page-header">
        <h1>My Bookings</h1>
        <p>Confirmed room bookings</p>
      </div>

      <div className="filters-row">
        <div className="form-group">
          <label>Agent</label>
          <select
            value={selectedAgent?.id || ''}
            onChange={(e) => {
              const a = agents.find((a) => a.id === e.target.value)
              if (a) setSelectedAgent(a)
            }}
          >
            {agents.map((a) => (
              <option key={a.id} value={a.id}>{a.name}</option>
            ))}
          </select>
        </div>
      </div>

      {bookings.length === 0 ? (
        <div className="card text-secondary" style={{ padding: '2rem', textAlign: 'center' }}>
          No bookings yet.
        </div>
      ) : (
        <div className="card">
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Room</th>
                  <th>Location</th>
                  <th>Time</th>
                  <th>Price</th>
                  <th>Booked At</th>
                </tr>
              </thead>
              <tbody>
                {bookings.map((b) => (
                  <tr key={b.id}>
                    <td>{b.room_name || '—'}</td>
                    <td>{b.location || '—'}</td>
                    <td>{formatDateTime(b.start_time)}{b.end_time ? ` — ${formatDateTime(b.end_time)}` : ''}</td>
                    <td className="mono price">{b.price != null ? `${b.price.toFixed(1)} tokens` : '—'}</td>
                    <td>{formatDateTime(b.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

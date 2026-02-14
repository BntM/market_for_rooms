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
      if (data.length > 0) setSelectedAgent(data[0])
    }).catch(() => {}).finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    if (selectedAgent) {
      api.getAgentBookings(selectedAgent.id).then(setBookings).catch(() => setBookings([]))
    }
  }, [selectedAgent?.id])

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
                  <th>Booking ID</th>
                  <th>Time Slot</th>
                  <th>Bid ID</th>
                  <th>Booked At</th>
                </tr>
              </thead>
              <tbody>
                {bookings.map((b) => (
                  <tr key={b.id}>
                    <td className="mono" style={{ fontSize: '0.75rem' }}>{b.id.slice(0, 8)}...</td>
                    <td className="mono" style={{ fontSize: '0.75rem' }}>{b.time_slot_id.slice(0, 8)}...</td>
                    <td className="mono" style={{ fontSize: '0.75rem' }}>{b.bid_id.slice(0, 8)}...</td>
                    <td>{new Date(b.created_at).toLocaleString()}</td>
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

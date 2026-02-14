import { useState, useEffect } from 'react'
import api from '../api'

export default function MyOrders() {
  const [agents, setAgents] = useState([])
  const [selectedAgent, setSelectedAgent] = useState(null)
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getAgents().then((data) => {
      setAgents(data)
      if (data.length > 0) setSelectedAgent(data[0])
    }).catch(() => {}).finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    if (selectedAgent) {
      api.getAgentLimitOrders(selectedAgent.id).then(setOrders).catch(() => setOrders([]))
    }
  }, [selectedAgent?.id])

  const handleCancel = async (orderId) => {
    try {
      await api.cancelLimitOrder(orderId)
      setOrders(orders.map((o) => o.id === orderId ? { ...o, status: 'cancelled' } : o))
    } catch (e) {
      alert(e.message)
    }
  }

  if (loading) return <div className="text-secondary">Loading...</div>

  return (
    <div>
      <div className="page-header">
        <h1>My Orders</h1>
        <p>Pending and past limit orders</p>
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

      {orders.length === 0 ? (
        <div className="card text-secondary" style={{ padding: '2rem', textAlign: 'center' }}>
          No limit orders yet.
        </div>
      ) : (
        <div className="card">
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Order ID</th>
                  <th>Time Slot</th>
                  <th>Max Price</th>
                  <th>Status</th>
                  <th>Created</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {orders.map((o) => (
                  <tr key={o.id}>
                    <td className="mono" style={{ fontSize: '0.75rem' }}>{o.id.slice(0, 8)}...</td>
                    <td className="mono" style={{ fontSize: '0.75rem' }}>{o.time_slot_id.slice(0, 8)}...</td>
                    <td className="mono price">{o.max_price.toFixed(1)}</td>
                    <td><span className={`status status--${o.status}`}>{o.status}</span></td>
                    <td>{new Date(o.created_at).toLocaleString()}</td>
                    <td>
                      {o.status === 'pending' && (
                        <button className="btn btn--danger btn--small" onClick={() => handleCancel(o.id)}>
                          Cancel
                        </button>
                      )}
                    </td>
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

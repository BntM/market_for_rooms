import { useState, useEffect } from 'react'
import api from '../api'
import PriceChart from '../components/PriceChart'

export default function PriceMonitor() {
  const [resources, setResources] = useState([])
  const [selectedResource, setSelectedResource] = useState(null)
  const [auctions, setAuctions] = useState([])
  const [selectedAuction, setSelectedAuction] = useState(null)
  const [priceHistory, setPriceHistory] = useState([])

  useEffect(() => {
    api.getResources().then((data) => {
      setResources(data)
      if (data.length > 0) setSelectedResource(data[0])
    }).catch(() => {})
  }, [])

  useEffect(() => {
    if (selectedResource) {
      api.getAuctions({ resource_id: selectedResource.id }).then((data) => {
        setAuctions(data)
        if (data.length > 0) setSelectedAuction(data[0])
        else setSelectedAuction(null)
      }).catch(() => { setAuctions([]); setSelectedAuction(null) })
    }
  }, [selectedResource?.id])

  useEffect(() => {
    if (selectedAuction) {
      api.getPriceHistory(selectedAuction.id).then(setPriceHistory).catch(() => setPriceHistory([]))
    } else {
      setPriceHistory([])
    }
  }, [selectedAuction?.id])

  return (
    <div>
      <div className="page-header">
        <h1>Price Monitor</h1>
        <p>Track auction price history per room</p>
      </div>

      <div className="filters-row">
        <div className="form-group">
          <label>Room</label>
          <select
            value={selectedResource?.id || ''}
            onChange={(e) => {
              const r = resources.find((r) => r.id === e.target.value)
              if (r) setSelectedResource(r)
            }}
          >
            {resources.map((r) => (
              <option key={r.id} value={r.id}>{r.name} — {r.location}</option>
            ))}
          </select>
        </div>
        <div className="form-group">
          <label>Auction</label>
          <select
            value={selectedAuction?.id || ''}
            onChange={(e) => {
              const a = auctions.find((a) => a.id === e.target.value)
              if (a) setSelectedAuction(a)
            }}
          >
            {auctions.length === 0 && <option value="">No auctions</option>}
            {auctions.map((a) => (
              <option key={a.id} value={a.id}>
                {a.id.slice(0, 8)}... — {a.status} — {a.current_price.toFixed(1)} tokens
              </option>
            ))}
          </select>
        </div>
      </div>

      {selectedAuction && (
        <div className="stats-row">
          <div className="card card--stat">
            <div className="label">Current Price</div>
            <div className="value">{selectedAuction.current_price.toFixed(1)}</div>
          </div>
          <div className="card card--stat">
            <div className="label">Start Price</div>
            <div className="value">{selectedAuction.start_price.toFixed(1)}</div>
          </div>
          <div className="card card--stat">
            <div className="label">Min Price</div>
            <div className="value">{selectedAuction.min_price.toFixed(1)}</div>
          </div>
          <div className="card card--stat">
            <div className="label">Status</div>
            <div className="value" style={{ fontSize: '1.25rem' }}>
              <span className={`status status--${selectedAuction.status}`}>{selectedAuction.status}</span>
            </div>
          </div>
        </div>
      )}

      <div className="card">
        {priceHistory.length > 0 ? (
          <PriceChart data={priceHistory} height={400} />
        ) : (
          <div className="text-secondary" style={{ padding: '3rem', textAlign: 'center' }}>
            {selectedAuction ? 'No price data yet. Tick the auction to generate price history.' : 'Select a room and auction to view prices.'}
          </div>
        )}
      </div>
    </div>
  )
}

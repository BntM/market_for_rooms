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
        setSelectedAuction(data.length > 0 ? data[0] : null)
      }).catch(() => {
        setAuctions([])
        setSelectedAuction(null)
      })
    }
  }, [selectedResource?.id])

  useEffect(() => {
    if (selectedAuction) {
      api.getPriceHistory(selectedAuction.id)
        .then(setPriceHistory)
        .catch(() => setPriceHistory([]))
    } else {
      setPriceHistory([])
    }
  }, [selectedAuction?.id])

  const formatDateTime = (isoStr) => {
    const d = new Date(isoStr)
    return d.toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
  }

  const timeLabels = priceHistory.map((p) =>
    p.recorded_at ? formatDateTime(p.recorded_at) : null
  ).filter(Boolean)

  return (
    <div>
      <div className="page-header">
        <h1>Price Monitor</h1>
        <p>Track dynamic pricing per room and auction</p>
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
                {a.auction_type} — {a.status} — {a.current_price?.toFixed(1)} tokens
              </option>
            ))}
          </select>
        </div>
      </div>

      {selectedAuction && (
        <div className="stats-row" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
          <div className="card" style={{ padding: '1rem', textAlign: 'center' }}>
            <div className="text-secondary" style={{ fontSize: '0.75rem', marginBottom: '0.25rem' }}>Current Price</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 700 }}>{selectedAuction.current_price?.toFixed(1)}</div>
          </div>
          <div className="card" style={{ padding: '1rem', textAlign: 'center' }}>
            <div className="text-secondary" style={{ fontSize: '0.75rem', marginBottom: '0.25rem' }}>Start Price</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 700 }}>{selectedAuction.start_price?.toFixed(1)}</div>
          </div>
          <div className="card" style={{ padding: '1rem', textAlign: 'center' }}>
            <div className="text-secondary" style={{ fontSize: '0.75rem', marginBottom: '0.25rem' }}>Min Price</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 700 }}>{selectedAuction.min_price?.toFixed(1)}</div>
          </div>
          <div className="card" style={{ padding: '1rem', textAlign: 'center' }}>
            <div className="text-secondary" style={{ fontSize: '0.75rem', marginBottom: '0.25rem' }}>Status</div>
            <div className={`status status--${selectedAuction.status}`} style={{ fontSize: '0.9rem' }}>{selectedAuction.status}</div>
          </div>
        </div>
      )}

      <div className="card">
        {priceHistory.length > 0 ? (
          <PriceChart data={priceHistory} labels={timeLabels.length > 0 ? timeLabels : undefined} height={400} />
        ) : (
          <div className="text-secondary" style={{ padding: '3rem', textAlign: 'center' }}>
            {selectedAuction ? 'No price data for this auction yet.' : selectedResource ? 'Select an auction to view price history.' : 'Select a room to view price history.'}
          </div>
        )}
      </div>
    </div>
  )
}

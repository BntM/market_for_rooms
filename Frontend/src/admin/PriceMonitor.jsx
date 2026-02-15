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
    }).catch(() => { })
  }, [])

  useEffect(() => {
    if (selectedResource) {
      // Get market price history directly, or fetch all auctions and aggregate?
      // "run simulation round dosent work for the price history on the admin dash... no auction involved"
      // "prices will just adjust each day based upon the customer booking behavior"
      // This implies we should be looking at `PriceHistory` but not optionally filtering by ONE auction.
      // Or maybe we treat the "market price" as the aggregated price history for that resource. 
      // The current backend/charts link PriceHistory to `time_slot_id` or `auction_id`.
      // The simulation creates bookings, which might create transactions, but does it create PriceHistory?
      // `app/services/market_simulator.py` (ported logic) might create price points?
      // The `god/auto-populate` endpoint DEFINITELY creates PriceHistory entries.
      // So let's fetch PriceHistory by Resource ID (requires new API or filtering).
      // The current API `getAuctions` -> `getPriceHistory` flow assumes auctions.

      // I'll update it to fetch "Resource Price History".
      // Since we don't have a direct endpoint for "Resource Price History", I'll mock it or use 
      // the existing generic market history if strictly for simulation, 
      // BUT for specific rooms, we need a way to see that room's price.
      // For now, let's look at `api.getResourceSchedule(id)`? No. 
      // Let's modify the frontend to iterate through time slots? Too heavy.
      // Best bet: The `god` mode populated `PriceHistory` with `time_slot_id`.
      // The `PriceHistory` model has `time_slot_id`.
      // So we need an endpoint `GET /api/resources/{id}/price-history`.

      // Let's assume I'll add that backend endpoint next.
      // For now, I will write the frontend assuming `api.getResourcePriceHistory(id)` exists.
      api.getResourcePriceHistory(selectedResource.id)
        .then(setPriceHistory)
        .catch(() => setPriceHistory([]))
    }
  }, [selectedResource?.id])

  return (
    <div>
      <div className="page-header">
        <h1>Price Monitor</h1>
        <p>Track dynamic pricing per room</p>
      </div>

      <div className="filters-row">
        <div className="form-group" style={{ width: '100%' }}>
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
      </div>

      <div className="card">
        {priceHistory.length > 0 ? (
          <PriceChart data={priceHistory} height={400} />
        ) : (
          <div className="text-secondary" style={{ padding: '3rem', textAlign: 'center' }}>
            {selectedResource ? 'No price data found for this room.' : 'Select a room to view price history.'}
          </div>
        )}
      </div>
    </div>
  )
}

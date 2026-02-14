import { useState, useEffect } from 'react'
import api from '../api'
import PriceChart from '../components/PriceChart'

export default function SlotDetail({ slot, auctions, agent, onClose, onBuyNow, onSetOrder }) {
  const [priceHistory, setPriceHistory] = useState([])
  const [maxPrice, setMaxPrice] = useState('')

  const auction = slot ? auctions.find((a) => a.time_slot_id === slot.id) : null

  useEffect(() => {
    if (auction) {
      api.getPriceHistory(auction.id).then(setPriceHistory).catch(() => setPriceHistory([]))
      setMaxPrice('')
    }
  }, [auction?.id])

  const formatDateTime = (isoStr) => {
    const d = new Date(isoStr)
    return d.toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
  }

  return (
    <div className={`detail-panel${slot ? ' open' : ''}`}>
      <button className="detail-panel__close" onClick={onClose}>&times;</button>

      {slot && (
        <>
          <h3 style={{ marginTop: '0.5rem' }}>Slot Details</h3>
          <div className="text-secondary mt-1" style={{ fontSize: '0.85rem' }}>
            {formatDateTime(slot.start_time)} &mdash; {formatDateTime(slot.end_time)}
          </div>

          <div className={`status status--${slot.status}`} style={{ marginTop: '0.5rem' }}>
            {slot.status}
          </div>

          {auction && (
            <>
              <div className="detail-panel__price">
                <span className={auction.current_price > auction.min_price ? 'price--negative' : 'price--positive'}>
                  {auction.current_price.toFixed(1)}
                </span>
                <span style={{ fontSize: '0.9rem', color: 'var(--color-text-secondary)', marginLeft: '0.25rem' }}>tokens</span>
              </div>

              <div style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>
                Range: {auction.min_price.toFixed(1)} &mdash; {auction.start_price.toFixed(1)} | Step: {auction.price_step.toFixed(1)}
              </div>

              <div className="mt-2">
                <PriceChart data={priceHistory} height={120} mini />
              </div>

              {auction.status === 'active' && (
                <>
                  <div className="detail-panel__section">
                    <button className="btn btn--primary" style={{ width: '100%' }} onClick={() => onBuyNow(auction)}>
                      Buy Now at {auction.current_price.toFixed(1)} tokens
                    </button>
                    {agent && (
                      <div className="text-secondary mt-1" style={{ fontSize: '0.8rem', textAlign: 'center' }}>
                        Your balance: {agent.token_balance.toFixed(1)} tokens
                      </div>
                    )}
                  </div>

                  <div className="detail-panel__section">
                    <h4 style={{ marginBottom: '0.75rem' }}>Set Limit Order</h4>
                    <div className="form-group">
                      <label>Max Price</label>
                      <input
                        type="number"
                        step="0.1"
                        min="0"
                        value={maxPrice}
                        onChange={(e) => setMaxPrice(e.target.value)}
                        placeholder="Execute when price drops to..."
                      />
                    </div>
                    <button
                      className="btn"
                      style={{ width: '100%' }}
                      disabled={!maxPrice || parseFloat(maxPrice) <= 0}
                      onClick={() => onSetOrder(auction, parseFloat(maxPrice))}
                    >
                      Place Limit Order
                    </button>
                  </div>
                </>
              )}
            </>
          )}

          {!auction && slot.status === 'available' && (
            <div className="detail-panel__section text-secondary">
              No auction running for this slot yet.
            </div>
          )}
        </>
      )}
    </div>
  )
}

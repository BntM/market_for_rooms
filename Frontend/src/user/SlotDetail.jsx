import { useState } from 'react'

export default function SlotDetail({ slots, auctions, agent, onClose, onRemoveSlot, onBuyAll, onSetOrder, agents }) {
  const [maxPrice, setMaxPrice] = useState('')
  const [splitWith, setSplitWith] = useState('')

  const isOpen = slots && slots.length > 0

  // Filter potential split partners
  const potentialPartners = agent && agents ? agents.filter(a => a.id !== agent.id) : []

  const formatDateTime = (isoStr) => {
    const d = new Date(isoStr)
    return d.toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
  }

  const items = slots.map((slot) => {
    const auction = auctions.find((a) => a.time_slot_id === slot.id)
    return { slot, auction }
  })

  const activeItems = items.filter((item) => item.auction && item.auction.status === 'active')
  const totalPrice = activeItems.reduce((sum, item) => sum + item.auction.current_price, 0)

  return (
    <div className={`detail-panel${isOpen ? ' open' : ''}`}>
      <button className="detail-panel__close" onClick={onClose}>&times;</button>

      {isOpen && (
        <>
          <h3 style={{ marginTop: '0.5rem' }}>
            {slots.length === 1 ? 'Selected Slot' : `${slots.length} Slots Selected`}
          </h3>

          <div style={{ marginTop: '0.75rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {items.map(({ slot, auction }) => (
              <div key={slot.id} style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '0.5rem', background: 'var(--color-background)', borderRadius: '4px',
                fontSize: '0.85rem',
              }}>
                <div style={{ flex: 1 }}>
                  <div>{formatDateTime(slot.start_time)}</div>
                  {auction && (
                    <div style={{ fontSize: '0.8rem' }}>
                      <span className={auction.current_price > (auction.min_price || 0) ? 'price--negative' : 'price--positive'}>
                        {auction.current_price.toFixed(1)}
                      </span>
                      <span style={{ color: 'var(--color-text-secondary)', marginLeft: '0.25rem' }}>tokens</span>
                      <span style={{ color: 'var(--color-text-secondary)', marginLeft: '0.5rem' }}>({auction.status})</span>
                    </div>
                  )}
                  {agent && slot.booked_agent_ids?.includes(agent.id) && (
                    <div style={{ fontSize: '0.8rem', color: '#b8860b', fontWeight: 'bold', marginTop: '0.25rem' }}>
                      ✓ You have a booking for this slot
                    </div>
                  )}
                  {!auction && (
                    <div className="text-secondary" style={{ fontSize: '0.75rem' }}>No auction</div>
                  )}
                </div>
                <button
                  onClick={() => onRemoveSlot(slot)}
                  style={{
                    background: 'none', border: 'none', cursor: 'pointer',
                    fontSize: '1.1rem', color: 'var(--color-text-secondary)', padding: '0 0.25rem',
                  }}
                  title="Remove"
                >&times;</button>
              </div>
            ))}
          </div>

          {activeItems.length > 0 && (
            <>
              <div style={{ marginTop: '1rem', padding: '0.75rem', background: 'var(--color-background)', borderRadius: '4px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 600 }}>
                  <span>Total ({activeItems.length} slot{activeItems.length > 1 ? 's' : ''})</span>
                  <span>{totalPrice.toFixed(1)} tokens</span>
                </div>
                {agent && (
                  <div className="text-secondary" style={{ fontSize: '0.8rem', marginTop: '0.25rem' }}>
                    Your balance: {agent.token_balance.toFixed(1)} tokens
                  </div>
                )}

                {agent && (
                  <div className="form-group" style={{ marginTop: '1rem', marginBottom: 0 }}>
                    <label style={{ fontSize: '0.75rem' }}>Split cost with (50/50)</label>
                    <select
                      value={splitWith}
                      onChange={(e) => setSplitWith(e.target.value)}
                      style={{ fontSize: '0.85rem', padding: '0.3rem' }}
                    >
                      <option value="">No split (I pay full)</option>
                      {potentialPartners.map(a => (
                        <option key={a.id} value={a.id}>{a.name} ({a.token_balance.toFixed(1)})</option>
                      ))}
                    </select>
                    {splitWith && (
                      <div style={{ fontSize: '0.75rem', color: 'var(--color-accent)', marginTop: '0.25rem' }}>
                        You pay {(totalPrice / 2).toFixed(1)}, partner pays {(totalPrice / 2).toFixed(1)}
                      </div>
                    )}
                  </div>
                )}
              </div>

              <div className="detail-panel__section">
                <button
                  className="btn btn--primary"
                  style={{ width: '100%' }}
                  onClick={() => onBuyAll(slots, { splitWith })}
                >
                  Buy {activeItems.length > 1 ? `All ${activeItems.length} Slots` : 'Now'} — {splitWith ? (totalPrice / 2).toFixed(1) : totalPrice.toFixed(1)} tokens {splitWith ? '(your share)' : ''}
                </button>
              </div>

              {/* Limit order for single slot */}
              {slots.length === 1 && activeItems.length === 1 && (
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
                    onClick={() => onSetOrder(activeItems[0].auction, parseFloat(maxPrice))}
                  >
                    Place Limit Order
                  </button>
                </div>
              )}
            </>
          )}

          {activeItems.length === 0 && (
            <div className="detail-panel__section text-secondary">
              No active auctions for selected slot(s).
            </div>
          )}
        </>
      )}
    </div>
  )
}

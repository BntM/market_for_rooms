import { useMemo } from 'react'

export default function RoomTimeGrid({ resources, auctions, selectedSlots, onToggleSlot, simDate, currentAgentId }) {

  // Process auctions into a resource-time map
  const { slotsByResource, sortedTimes } = useMemo(() => {
    const map = {}
    const times = new Set()

    // Initialize map for all resources (even empty ones)
    resources.forEach(r => { map[r.id] = {} })

    auctions.forEach(auction => {
      const slot = auction.time_slot
      if (slot && map[slot.resource_id]) {
        map[slot.resource_id][slot.start_time] = { slot, auction }
        times.add(slot.start_time)
      }
    })

    return {
      slotsByResource: map,
      sortedTimes: [...times].sort()
    }
  }, [resources, auctions])

  if (sortedTimes.length === 0) {
    return (
      <div className="card text-secondary" style={{ padding: '2rem', textAlign: 'center' }}>
        No time slots found for the selected date.
      </div>
    )
  }

  const formatTime = (isoStr) => {
    const d = new Date(isoStr)
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  const formatDate = (isoStr) => {
    const d = new Date(isoStr)
    return d.toLocaleDateString([], { month: 'short', day: 'numeric' })
  }

  const legend = (
    <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem', fontSize: '0.8rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
        <div style={{ width: 12, height: 12, border: '2px dotted var(--color-primary)', background: '#fff5f5' }}></div>
        <span>Selected</span>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
        <div style={{ width: 12, height: 12, border: '2px solid #ffd700', background: 'rgba(255, 215, 0, 0.1)' }}></div>
        <span>Your Booking</span>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
        <div style={{ width: 12, height: 12, background: 'rgba(180, 180, 180, 0.3)' }}></div>
        <span>Fully Booked</span>
      </div>
    </div>
  )

  return (
    <>
      {legend}
      <div className="table-wrap" style={{ paddingBottom: '1rem' }}>
        <div className="room-grid" style={{ gridTemplateColumns: `160px repeat(${sortedTimes.length}, minmax(80px, 1fr))`, minWidth: 'max-content' }}>
          {/* Header row */}
          <div className="room-grid__header" />
          {sortedTimes.map((t) => (
            <div key={t} className="room-grid__header">
              <div>{formatDate(t)}</div>
              <div>{formatTime(t)}</div>
            </div>
          ))}

          {/* Data rows */}
          {resources.map((r) => {
            const rowData = slotsByResource[r.id] || {}

            return [
              <div key={`label-${r.id}`} className="room-grid__row-label">
                <div>
                  <div>{r.name}</div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--color-text-secondary)', fontFamily: 'var(--font-body)' }}>
                    {r.location} (Cap: {r.capacity})
                  </div>
                </div>
              </div>,
              ...sortedTimes.map((t) => {
                const cellData = rowData[t]
                const isPast = simDate && new Date(t) < simDate

                if (!cellData) {
                  return <div key={`${r.id}-${t}`} className="room-grid__cell" style={{ background: '#f5f5f3', opacity: isPast ? 0.4 : 1 }}>
                    <span className="text-secondary" style={{ fontSize: '0.7rem' }}>—</span>
                  </div>
                }

                const { slot, auction } = cellData
                const isSelected = selectedSlots.some((s) => s.id === slot.id)
                const isBooked = slot.status === 'booked'
                const isUserBooked = currentAgentId && slot.booked_agent_ids?.includes(currentAgentId)
                const isActive = auction?.status === 'active'
                const isUnavailable = isPast || (isBooked && !isUserBooked)

                return (
                  <div
                    key={`${r.id}-${t}`}
                    className={`room-grid__cell${isSelected ? ' selected' : ''}${isBooked ? ' booked' : ''}${isUserBooked ? ' user-booked' : ''}`}
                    onClick={() => !isUnavailable && onToggleSlot(slot)}
                    style={{
                      ...(isUnavailable ? { cursor: 'default' } : {}),
                      ...(isPast ? { opacity: 0.4 } : {}),
                      ...(isUserBooked ? { border: '2px solid #ffd700', background: 'rgba(255, 215, 0, 0.1)', color: '#b8860b' } : {}),
                    }}
                  >
                    {isUserBooked ? (
                      <span style={{ fontSize: '0.7rem', fontWeight: 'bold' }}>✓ Your Booking</span>
                    ) : isPast && !isBooked ? (
                      <span className="text-secondary" style={{ fontSize: '0.7rem' }}>Past</span>
                    ) : isBooked ? (
                      <span style={{ fontSize: '0.7rem' }}>Fully Booked</span>
                    ) : auction ? (
                      <>
                        <span className={`cell-price ${isActive ? 'price--negative' : ''}`}>
                          {auction.current_price.toFixed(1)}
                        </span>
                        <span style={{ fontSize: '0.6rem', color: 'var(--color-text-secondary)' }}>
                          {auction.status}
                        </span>
                      </>
                    ) : (
                      <span className="text-secondary" style={{ fontSize: '0.7rem' }}>
                        {slot.status}
                      </span>
                    )}
                  </div>
                )
              }),
            ]
          })}
        </div>
      </div>
    </>
  )
}

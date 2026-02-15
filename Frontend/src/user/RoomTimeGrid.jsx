import { useMemo } from 'react'

export default function RoomTimeGrid({ resources, auctions, selectedSlots, onToggleSlot }) {

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

  return (
    <>
      <div style={{ overflowX: 'auto', paddingBottom: '1rem' }}>
        <div className="room-grid" style={{ gridTemplateColumns: `160px repeat(${sortedTimes.length}, minmax(80px, 1fr))`, minWidth: '100%' }}>
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
                    {r.location}
                  </div>
                </div>
              </div>,
              ...sortedTimes.map((t) => {
                const cellData = rowData[t]

                if (!cellData) {
                  return <div key={`${r.id}-${t}`} className="room-grid__cell" style={{ background: '#f5f5f3' }}>
                    <span className="text-secondary" style={{ fontSize: '0.7rem' }}>—</span>
                  </div>
                }

                const { slot, auction } = cellData
                const isSelected = selectedSlots.some((s) => s.id === slot.id)
                const isBooked = slot.status === 'booked'
                const isActive = auction?.status === 'active'

                return (
                  <div
                    key={`${r.id}-${t}`}
                    className={`room-grid__cell${isSelected ? ' selected' : ''}${isBooked ? ' booked' : ''}`}
                    onClick={() => !isBooked && onToggleSlot(slot)}
                    style={isBooked ? { cursor: 'default' } : undefined}
                  >
                    {isBooked ? (
                      <span style={{ fontSize: '0.7rem' }}>Booked</span>
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

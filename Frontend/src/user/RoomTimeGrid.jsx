import { useState, useEffect } from 'react'
import api from '../api'

export default function RoomTimeGrid({ resources, auctions, selectedSlot, onSelectSlot }) {
  const [slotsByResource, setSlotsByResource] = useState({})

  useEffect(() => {
    const loadSlots = async () => {
      const result = {}
      for (const r of resources) {
        try {
          const slots = await api.getTimeSlots(r.id)
          result[r.id] = slots
        } catch {
          result[r.id] = []
        }
      }
      setSlotsByResource(result)
    }
    if (resources.length > 0) loadSlots()
  }, [resources])

  // Collect all unique time slots across resources
  const allTimes = new Set()
  Object.values(slotsByResource).forEach((slots) => {
    slots.forEach((s) => allTimes.add(s.start_time))
  })
  const sortedTimes = [...allTimes].sort()

  if (sortedTimes.length === 0) {
    return (
      <div className="card text-secondary" style={{ padding: '2rem', textAlign: 'center' }}>
        No time slots generated yet. Admin needs to generate time slots for rooms.
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

  // Group times by date for header
  const auctionBySlot = {}
  auctions.forEach((a) => {
    auctionBySlot[a.time_slot_id] = a
  })

  const cols = sortedTimes.length + 1 // +1 for row labels

  return (
    <div className="room-grid" style={{ gridTemplateColumns: `160px repeat(${sortedTimes.length}, minmax(80px, 1fr))` }}>
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
        const slots = slotsByResource[r.id] || []
        const slotMap = {}
        slots.forEach((s) => { slotMap[s.start_time] = s })

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
            const slot = slotMap[t]
            if (!slot) {
              return <div key={`${r.id}-${t}`} className="room-grid__cell" style={{ background: '#f5f5f3' }}>
                <span className="text-secondary" style={{ fontSize: '0.7rem' }}>—</span>
              </div>
            }

            const auction = auctionBySlot[slot.id]
            const isSelected = selectedSlot?.id === slot.id
            const isBooked = slot.status === 'booked'
            const isActive = auction?.status === 'active'

            return (
              <div
                key={`${r.id}-${t}`}
                className={`room-grid__cell${isSelected ? ' selected' : ''}${isBooked ? ' booked' : ''}`}
                onClick={() => onSelectSlot(slot)}
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
  )
}

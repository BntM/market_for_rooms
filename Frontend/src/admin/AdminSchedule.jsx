import { useState, useEffect } from 'react'
import api from '../api'
import RoomTimeGrid from '../user/RoomTimeGrid'
import SlotDetail from '../user/SlotDetail'

export default function AdminSchedule() {
    const [resources, setResources] = useState([])
    const [auctions, setAuctions] = useState([])
    const [selectedSlot, setSelectedSlot] = useState(null)
    const [location, setLocation] = useState('')
    const [loading, setLoading] = useState(true)
    const [viewDate, setViewDate] = useState(new Date())

    const load = async () => {
        setLoading(true)
        try {
            const start = new Date(viewDate)
            start.setHours(0, 0, 0, 0)
            const end = new Date(viewDate)
            end.setHours(23, 59, 59, 999)

            const [res, auc] = await Promise.all([
                api.getResources(),
                api.getAuctions({ start_date: start.toISOString(), end_date: end.toISOString() }),
            ])
            setResources(res)
            setAuctions(auc)
        } catch (e) {
            console.error(e)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => { load() }, [viewDate])

    const handleDateChange = (days) => {
        const next = new Date(viewDate)
        next.setDate(next.getDate() + days)
        setViewDate(next)
    }

    const locations = [...new Set(resources.map((r) => r.location).filter(Boolean))]
    const filtered = location
        ? resources.filter((r) => r.location === location)
        : resources

    return (
        <div>
            <div className="page-header">
                <h1>Schedule & Availability</h1>
                <p>View market status and active auctions.</p>
            </div>

            <div className="filters-row" style={{ alignItems: 'flex-end' }}>
                <div className="form-group">
                    <label>Date</label>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <button
                            className="btn btn--small"
                            onClick={() => handleDateChange(-1)}
                        >&lt;</button>
                        <div style={{
                            background: 'white',
                            padding: '0.5rem 1rem',
                            border: '1px solid #ddd',
                            borderRadius: '4px',
                            fontWeight: 500,
                            minWidth: '140px',
                            textAlign: 'center'
                        }}>
                            {viewDate.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' })}
                        </div>
                        <button
                            className="btn btn--small"
                            onClick={() => handleDateChange(1)}
                        >&gt;</button>
                    </div>
                </div>

                <div className="form-group">
                    <label>Location</label>
                    <select value={location} onChange={(e) => setLocation(e.target.value)}>
                        <option value="">All locations</option>
                        {locations.map((l) => (
                            <option key={l} value={l}>{l}</option>
                        ))}
                    </select>
                </div>
            </div>

            {loading ? (
                <div className="text-secondary" style={{ padding: '2rem' }}>Loading schedule...</div>
            ) : filtered.length === 0 ? (
                <div className="card text-secondary" style={{ padding: '3rem', textAlign: 'center' }}>
                    No rooms available.
                </div>
            ) : (
                <RoomTimeGrid
                    resources={filtered}
                    auctions={auctions}
                    selectedSlot={selectedSlot}
                    onSelectSlot={setSelectedSlot}
                />
            )}

            <SlotDetail
                slot={selectedSlot}
                auctions={auctions}
                agent={null} // logic checks for agent to show buy button
                onClose={() => setSelectedSlot(null)}
                onBuyNow={() => { }}
                onSetOrder={() => { }}
            />
        </div>
    )
}

import { useState, useEffect } from 'react'
import api from '../api'

export default function RoomManager() {
  const [resources, setResources] = useState([])
  const [slots, setSlots] = useState({})
  const [showAdd, setShowAdd] = useState(false)
  const [form, setForm] = useState({ name: '', location: '', capacity: 10 })
  const [slotForm, setSlotForm] = useState({ start_date: '', end_date: '', daily_start_hour: 9, daily_end_hour: 17 })
  const [genTarget, setGenTarget] = useState(null)
  const [loading, setLoading] = useState(true)

  const load = async () => {
    try {
      const res = await api.getResources()
      setResources(res)
      const slotMap = {}
      for (const r of res) {
        try {
          slotMap[r.id] = await api.getTimeSlots(r.id)
        } catch { slotMap[r.id] = [] }
      }
      setSlots(slotMap)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const handleAdd = async (e) => {
    e.preventDefault()
    try {
      await api.createResource({ ...form, resource_type: 'room' })
      setForm({ name: '', location: '', capacity: 10 })
      setShowAdd(false)
      await load()
    } catch (e) {
      alert(e.message)
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('Delete this room?')) return
    try {
      await api.deleteResource(id)
      await load()
    } catch (e) {
      alert(e.message)
    }
  }

  const handleGenerate = async (e) => {
    e.preventDefault()
    if (!genTarget) return
    try {
      await api.generateTimeSlots(genTarget, slotForm)
      setGenTarget(null)
      await load()
    } catch (e) {
      alert(e.message)
    }
  }

  const handleImport = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    const formData = new FormData()
    formData.append('file', file)
    try {
      setLoading(true)
      const res = await api.importResources(formData)
      alert(`Imported ${res.resources_created} rooms and ${res.time_slots_created} slots!`)
      await load()
    } catch (e) {
      alert(e.message)
      setLoading(false)
    }
  }

  if (loading) return <div className="text-secondary">Loading rooms...</div>

  return (
    <div>
      <div className="flex-between mb-2">
        <div className="page-header" style={{ marginBottom: 0 }}>
          <h1>Room Manager</h1>
          <p>Manage rooms and generate time slots</p>
        </div>
        <div className="flex gap-1">
          <button className="btn btn--danger" onClick={async () => {
            if (confirm('Are you sure you want to DELETE ALL ROOMS? This cannot be undone.')) {
              try {
                await api.deleteAllResources()
                await load()
              } catch (e) { alert(e.message) }
            }
          }}>Delete All</button>
          <label className="btn btn--secondary" style={{ cursor: 'pointer' }}>
            Import CSV
            <input type="file" accept=".csv" style={{ display: 'none' }} onChange={handleImport} />
          </label>
          <button className="btn btn--primary" onClick={() => setShowAdd(!showAdd)}>
            {showAdd ? 'Cancel' : 'Add Room'}
          </button>
        </div>
      </div>

      <div className="card mb-2">
        <h3>🤖 Auto-Price (Admin)</h3>
        <p className="text-secondary small">Apply the latest ML model (trained by God Mode) to set base prices for all rooms.</p>
        <div className="flex gap-1 mt-1">
          <input type="date" id="auto_price_date" />
          <button className="btn btn--primary" onClick={async () => {
            const date = document.getElementById('auto_price_date').value
            if (!date) return alert('Select date')
            // Fetch analysis first to get weights
            // In a real app we'd store "active model" in DB. 
            // For hackathon, we'll re-analyze or assume model exists in session/cache or let user re-upload?
            // The user said "based upon the model that the god user decides". 
            // Be pragmatic: We'll assume the God Mode action ALREADY populated the DB with prices.
            // Or does the user mean Admin triggers the population?
            // "admin user... should have an autoprice option... based upon the model the god user decides"
            // This implies God TRAINS/DECIDES, Admin EXECUTES.
            // Let's call the same God Endpoint but expose it here.
            // We need the analysis results. Let's fetch them from a new endpoint or LocalStorage? 
            // Simplest: We'll just call the auto-populate if we can. 
            // But wait, auto-populate needs analysis results. 
            // Let's just create a quick "Get Latest Analysis" endpoint or store it in DB.
            // Plan B: Admin uploads the CSV too or we just share the endpoint.

            // Actually, the God Mode auto-populate DOES the pricing and slot creation.
            // So if God ran it, it's done. 
            // If Admin wants to run it, they need the analysis.
            // Let's assume the CSV was uploaded to /history/analyze recently and cached? No stateless.

            // Let's just make the Admin call the /god/auto-populate but we need the weights.
            // I'll make GodTools save the weights to localStorage or DB?
            // Better: Add an endpoint to "GET /api/god/model" that returns last training.
            // For now, let's just alert the user to use God Mode if they want full ML control, 
            // OR simply call the optimization endpoint which is similar? 

            // User request: "admin user... should have an autoprice option... based upon the model that the god user decides"
            // I will call a new endpoint `apply-latest-model` and assumes God saved it.
            try {
              const res = await api.autoPopulateMarket({ end_date: date, use_saved_model: true })
              alert(res.message)
              await load()
            } catch (e) { alert(e.message) }
          }}>Apply Pricing Model</button>
        </div>
      </div>

      {showAdd && (
        <div className="card mb-2">
          <h3 style={{ marginBottom: '1rem' }}>New Room</h3>
          <form onSubmit={handleAdd}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 120px auto', gap: '1rem', alignItems: 'end' }}>
              <div className="form-group">
                <label>Name</label>
                <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
              </div>
              <div className="form-group">
                <label>Location</label>
                <input value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })} required />
              </div>
              <div className="form-group">
                <label>Capacity</label>
                <input type="number" min="1" value={form.capacity} onChange={(e) => setForm({ ...form, capacity: parseInt(e.target.value) || 1 })} />
              </div>
              <button className="btn btn--primary" type="submit">Create</button>
            </div>
          </form>
        </div>
      )}

      {genTarget && (
        <div className="card mb-2">
          <h3 style={{ marginBottom: '1rem' }}>
            Generate Time Slots for {resources.find((r) => r.id === genTarget)?.name}
          </h3>
          <form onSubmit={handleGenerate}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 100px 100px auto', gap: '1rem', alignItems: 'end' }}>
              <div className="form-group">
                <label>Start Date</label>
                <input type="date" value={slotForm.start_date} onChange={(e) => setSlotForm({ ...slotForm, start_date: e.target.value })} required />
              </div>
              <div className="form-group">
                <label>End Date</label>
                <input type="date" value={slotForm.end_date} onChange={(e) => setSlotForm({ ...slotForm, end_date: e.target.value })} required />
              </div>
              <div className="form-group">
                <label>From Hour</label>
                <input type="number" min="0" max="23" value={slotForm.daily_start_hour} onChange={(e) => setSlotForm({ ...slotForm, daily_start_hour: parseInt(e.target.value) })} />
              </div>
              <div className="form-group">
                <label>To Hour</label>
                <input type="number" min="0" max="23" value={slotForm.daily_end_hour} onChange={(e) => setSlotForm({ ...slotForm, daily_end_hour: parseInt(e.target.value) })} />
              </div>
              <div className="flex gap-1">
                <button className="btn btn--primary" type="submit">Generate</button>
                <button className="btn" type="button" onClick={() => setGenTarget(null)}>Cancel</button>
              </div>
            </div>
          </form>
        </div>
      )}

      <div className="card">
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Location</th>
                <th>Capacity</th>
                <th>Time Slots</th>
                <th>Status Breakdown</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {resources.length === 0 ? (
                <tr><td colSpan={6} className="text-secondary" style={{ textAlign: 'center' }}>No rooms yet</td></tr>
              ) : resources.map((r) => {
                const rs = slots[r.id] || []
                const available = rs.filter((s) => s.status === 'available').length
                const inAuction = rs.filter((s) => s.status === 'in_auction').length
                const booked = rs.filter((s) => s.status === 'booked').length
                return (
                  <tr key={r.id}>
                    <td style={{ fontWeight: 500 }}>{r.name}</td>
                    <td>{r.location}</td>
                    <td className="mono">{r.capacity}</td>
                    <td className="mono">{rs.length}</td>
                    <td style={{ fontSize: '0.8rem' }}>
                      <span className="status status--active">{available} avail</span>{' '}
                      <span className="status status--pending">{inAuction} auction</span>{' '}
                      <span className="status status--completed">{booked} booked</span>
                    </td>
                    <td>
                      <div className="flex gap-1">
                        <button className="btn btn--small" onClick={() => setGenTarget(r.id)}>Slots</button>
                        <button className="btn btn--danger btn--small" onClick={() => handleDelete(r.id)}>Delete</button>
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

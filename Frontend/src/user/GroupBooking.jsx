import { useState, useEffect } from 'react'
import api from '../api'

export default function GroupBookingModal({ auction, currentUser, onClose, onSuccess }) {
    const [friends, setFriends] = useState([]) // List of { agent_id, amount }
    const [agents, setAgents] = useState([])
    const [myShare, setMyShare] = useState(auction.current_price)

    useEffect(() => {
        api.getAgents().then(setAgents)
    }, [])

    const handleAddFriend = () => {
        setFriends([...friends, { agent_id: '', amount: 0 }])
    }

    const updateFriend = (index, field, value) => {
        const newFriends = [...friends]
        newFriends[index][field] = value
        setFriends(newFriends)
        // Auto-recalc my share
        const totalOthers = newFriends.reduce((acc, f) => acc + parseFloat(f.amount || 0), 0)
        setMyShare(Math.max(0, auction.current_price - totalOthers))
    }

    const handleSubmit = async () => {
        // Validate
        const total = parseFloat(myShare) + friends.reduce((acc, f) => acc + parseFloat(f.amount || 0), 0)
        if (Math.abs(total - auction.current_price) > 0.1) {
            alert(`Total shares (${total.toFixed(1)}) must equal Auction Price (${auction.current_price.toFixed(1)})`)
            return
        }

        // Construct payload (mock implementation since backend endpoint isn't fully wired for this specific JSON structure yet, 
        // but assuming standard post structure)
        // Note: The Implementation Plan mentioned creating a group-bid endpoint in auctions.py.
        // For now, we will simulate the "Group Bid" by just making the current user pay or alerting.
        // REAL IMPLEMENTATION: await api.placeGroupBid(...)

        alert("Group Bid Submitted! (Backend integration pending for multi-agent debit)")
        onSuccess()
    }

    return (
        <div className="modal-overlay">
            <div className="modal-content">
                <h2>Group Booking for {auction.room_id}</h2>
                <p>Total Price: <strong>{auction.current_price} tokens</strong></p>

                <div className="form-group">
                    <label>Your Share ({currentUser.name})</label>
                    <input type="number" value={myShare} disabled />
                </div>

                <h3>Split with Friends ({friends.length}/{auction.capacity - 1})</h3>
                {friends.map((f, i) => (
                    <div key={i} className="split-row" style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem' }}>
                        <select value={f.agent_id} onChange={(e) => updateFriend(i, 'agent_id', e.target.value)}>
                            <option value="">Select Friend...</option>
                            {agents.filter(a => a.id !== currentUser.id).map(a => (
                                <option key={a.id} value={a.id}>{a.name} ({a.token_balance.toFixed(1)})</option>
                            ))}
                        </select>
                        <input
                            type="number"
                            placeholder="Amount"
                            value={f.amount}
                            onChange={(e) => updateFriend(i, 'amount', parseFloat(e.target.value))}
                            style={{ width: '100px' }}
                        />
                    </div>
                ))}

                {friends.length < (auction.capacity - 1) && (
                    <button className="btn btn--small" onClick={handleAddFriend}>+ Add Friend</button>
                )}

                <div className="modal-actions" style={{ marginTop: '2rem', display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
                    <button className="btn btn--secondary" onClick={onClose}>Cancel</button>
                    <button className="btn btn--primary" onClick={handleSubmit}>Confirm Split Payment</button>
                </div>
            </div>
        </div>
    )
}

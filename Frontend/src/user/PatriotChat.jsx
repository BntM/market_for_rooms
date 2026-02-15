import { useState } from 'react'
import api from '../api'

export default function PatriotChat({ onClose }) {
    const [message, setMessage] = useState('')
    const [history, setHistory] = useState([
        { role: 'system', text: 'Hi! I am Patriot AI. Ask me about GMU events, or ask me to generate images for your study group!' }
    ])
    const [loading, setLoading] = useState(false)

    const handleSend = async () => {
        if (!message.trim()) return

        const userMsg = { role: 'user', text: message }
        setHistory(prev => [...prev, userMsg])
        setMessage('')
        setLoading(true)

        try {
            const res = await api.request('/student/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: userMsg.text })
            })

            setHistory(prev => [...prev, { role: 'ai', text: res.response }])
        } catch (e) {
            setHistory(prev => [...prev, { role: 'ai', text: "Error connecting to Patriot AI service." }])
        } finally {
            setLoading(false)
        }
    }

    return (
        <div style={{
            position: 'fixed',
            bottom: '20px',
            right: '20px',
            width: '350px',
            height: '500px',
            backgroundColor: 'white',
            boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
            borderRadius: '12px',
            display: 'flex',
            flexDirection: 'column',
            zIndex: 1000,
            border: '1px solid #ddd'
        }}>
            <div style={{
                padding: '1rem',
                borderBottom: '1px solid #eee',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                background: '#006633', // GMU Green
                color: 'white',
                borderTopLeftRadius: '12px',
                borderTopRightRadius: '12px'
            }}>
                <div style={{ fontWeight: 'bold' }}>Patriot AI Assistant</div>
                <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'white', cursor: 'pointer', fontSize: '1.2rem' }}>×</button>
            </div>

            <div style={{ flex: 1, padding: '1rem', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '0.8rem' }}>
                {history.map((msg, i) => (
                    <div key={i} style={{
                        alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                        background: msg.role === 'user' ? '#f0f0f0' : '#e6ffe6',
                        padding: '0.8rem',
                        borderRadius: '8px',
                        maxWidth: '85%',
                        fontSize: '0.9rem',
                        whiteSpace: 'pre-wrap'
                    }}>
                        {msg.text}
                    </div>
                ))}
                {loading && <div style={{ alignSelf: 'flex-start', color: '#888', fontStyle: 'italic', fontSize: '0.8rem' }}>Patriot AI is thinking...</div>}
            </div>

            <div style={{ padding: '1rem', borderTop: '1px solid #eee', display: 'flex', gap: '0.5rem' }}>
                <input
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                    placeholder="Ask about events or generate images..."
                    style={{ flex: 1, padding: '0.6rem', border: '1px solid #ddd', borderRadius: '4px' }}
                />
                <button
                    onClick={handleSend}
                    disabled={loading}
                    style={{
                        background: '#ffcc33', // GMU Gold
                        border: 'none',
                        borderRadius: '4px',
                        padding: '0 1rem',
                        cursor: 'pointer',
                        fontWeight: 'bold',
                        color: '#333'
                    }}
                >
                    Send
                </button>
            </div>
        </div>
    )
}

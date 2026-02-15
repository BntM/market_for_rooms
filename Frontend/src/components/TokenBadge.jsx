import { useState, useEffect } from 'react'
import api from '../api'

export default function TokenBadge() {
  const [agents, setAgents] = useState([])
  const [selected, setSelected] = useState(null)

  useEffect(() => {
    api.getAgents().then((data) => {
      setAgents(data)
      const stored = localStorage.getItem('agent_id')
      if (stored) {
        const found = data.find(a => a.id === stored)
        if (found) { setSelected(found); return }
      }
      if (data.length > 0) {
        setSelected(data[0])
        localStorage.setItem('agent_id', data[0].id)
      }
    }).catch(() => { })
  }, [])

  if (!selected) return null

  return (
    <div className="token-badge" title={`Agent: ${selected.name}`}>
      <div className="token-badge__icon" />
      <span>{selected.token_balance.toFixed(1)}</span>
      <select
        value={selected.id}
        onChange={(e) => {
          const a = agents.find((a) => a.id === e.target.value)
          if (a) {
            setSelected(a)
            localStorage.setItem('agent_id', a.id)
            // Force reload or event dispatch might be needed if other components don't listen to storage
            // But for now, let's just save it.
            window.dispatchEvent(new Event('agent-changed'))
          }
        }}
        style={{
          border: 'none',
          background: 'transparent',
          fontFamily: 'var(--font-mono)',
          fontSize: '0.75rem',
          color: 'var(--color-text-secondary)',
          cursor: 'pointer',
          paddingRight: '0.25rem',
        }}
      >
        {agents.map((a) => (
          <option key={a.id} value={a.id}>{a.name}</option>
        ))}
      </select>
    </div>
  )
}

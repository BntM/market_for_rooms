import { useState, useEffect } from 'react'
import api from '../api'

export default function TokenBadge() {
  const [agents, setAgents] = useState([])
  const [selected, setSelected] = useState(null)

  useEffect(() => {
    api.getAgents().then((data) => {
      setAgents(data)
      if (data.length > 0 && !selected) {
        setSelected(data[0])
      }
    }).catch(() => {})
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
          if (a) setSelected(a)
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

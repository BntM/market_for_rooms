import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { useState, useEffect } from 'react'
import api from '../api'
import TokenBadge from './TokenBadge'

const userNav = [
  { to: '/user', label: 'Marketplace', end: true },
  { to: '/user/bookings', label: 'My Bookings' },
  { to: '/user/orders', label: 'My Orders' },
]

const adminNav = [
  { to: '/admin', label: 'Dashboard', end: true },
  { to: '/admin/rooms', label: 'Rooms' },
  { to: '/admin/prices', label: 'Prices' },
  { to: '/admin/pz-sim', label: 'Simulate' },
  { to: '/admin/init', label: 'Initialize' },
]

export default function Layout() {
  const location = useLocation()
  const isAdmin = location.pathname.startsWith('/admin')
  const nav = isAdmin ? adminNav : userNav

  const [simDate, setSimDate] = useState(null)

  const fetchDate = () => {
    api.getConfig().then(c => {
      if (c && c.current_simulation_date) {
        setSimDate(new Date(c.current_simulation_date))
      }
    }).catch(console.error)
  }

  useEffect(() => {
    fetchDate()
    // Listen for resets or advances
    const handleUpdate = (e) => {
      if (e.detail && e.detail.date) {
        setSimDate(new Date(e.detail.date))
      } else {
        fetchDate()
      }
    }
    window.addEventListener('simulation-reset', handleUpdate)
    // Poll every 5s just in case
    const interval = setInterval(fetchDate, 5000)
    return () => {
      window.removeEventListener('simulation-reset', handleUpdate)
      clearInterval(interval)
    }
  }, [])

  const handleResetTime = async () => {
    if (!window.confirm('Reset simulation to Feb 14?')) return
    try {
      await api.resetTime()
      await api.resetSimulation()
      window.dispatchEvent(new Event('simulation-reset'))
      fetchDate()
    } catch (e) {
      alert(e.message)
    }
  }

  return (
    <div className="app-shell">
      <header className="top-bar">
        <div className="top-bar__logo">
          Market <span>for</span> Rooms
        </div>

        <nav className="top-bar__nav">
          {nav.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="top-bar__right">
          {simDate && (
            <div style={{
              background: 'var(--color-highlight)',
              padding: '0.25rem 0.75rem',
              border: '1px solid var(--color-text)',
              fontSize: '0.85rem',
              fontWeight: 500,
              display: 'flex',
              gap: '0.5rem',
              alignItems: 'center',
              fontFamily: 'var(--font-mono)',
            }}>
              <span style={{ color: 'var(--color-text-secondary)', fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Sim</span>
              <span>
                {simDate.toLocaleDateString([], { month: 'short', day: 'numeric' })}
                {' '}
                {simDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
              <button
                onClick={handleResetTime}
                title="Reset to Feb 14"
                style={{
                  border: '1px solid var(--color-text)',
                  background: 'transparent',
                  padding: '1px 6px',
                  cursor: 'pointer',
                  fontSize: '0.65rem',
                  fontWeight: 500,
                  textTransform: 'uppercase',
                  letterSpacing: '0.03em',
                  fontFamily: 'var(--font-mono)',
                }}
              >
                Reset
              </button>
            </div>
          )}
          {!isAdmin && <TokenBadge />}
          <div className="mode-toggle">
            <NavLink to="/user" className={`mode-toggle__btn${!isAdmin ? ' active' : ''}`}>
              User
            </NavLink>
            <NavLink to="/admin" className={`mode-toggle__btn${isAdmin ? ' active' : ''}`}>
              Admin
            </NavLink>
          </div>
        </div>
      </header>
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  )
}

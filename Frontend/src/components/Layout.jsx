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
    const handleUpdate = () => fetchDate()
    window.addEventListener('simulation-reset', handleUpdate)
    // Poll every 5s just in case
    const interval = setInterval(fetchDate, 5000)
    return () => {
      window.removeEventListener('simulation-reset', handleUpdate)
      clearInterval(interval)
    }
  }, [])

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
              background: '#f0f0f0',
              padding: '0.25rem 0.75rem',
              borderRadius: '4px',
              fontSize: '0.9rem',
              fontWeight: 600,
              display: 'flex',
              gap: '0.5rem',
              alignItems: 'center',
              marginRight: '1rem'
            }}>
              <span style={{ color: '#666', fontSize: '0.8rem', textTransform: 'uppercase' }}>Current:</span>
              <span>
                {simDate.toLocaleDateString([], { month: 'short', day: 'numeric' })}
                {' '}
                {simDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
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

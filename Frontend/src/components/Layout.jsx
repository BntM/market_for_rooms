import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { useState } from 'react'
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
  { to: '/admin/config', label: 'Config' },
]

export default function Layout() {
  const location = useLocation()
  const isAdmin = location.pathname.startsWith('/admin')
  const nav = isAdmin ? adminNav : userNav

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

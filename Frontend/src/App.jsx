import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Marketplace from './user/Marketplace'
import MyBookings from './user/MyBookings'
import MyOrders from './user/MyOrders'
import AdminDashboard from './admin/AdminDashboard'
import RoomManager from './admin/RoomManager'
import AuctionConfig from './admin/AuctionConfig'
import PriceMonitor from './admin/PriceMonitor'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/user" replace />} />
      <Route element={<Layout />}>
        <Route path="/user" element={<Marketplace />} />
        <Route path="/user/bookings" element={<MyBookings />} />
        <Route path="/user/orders" element={<MyOrders />} />
        <Route path="/admin" element={<AdminDashboard />} />
        <Route path="/admin/rooms" element={<RoomManager />} />
        <Route path="/admin/config" element={<AuctionConfig />} />
        <Route path="/admin/prices" element={<PriceMonitor />} />
      </Route>
    </Routes>
  )
}

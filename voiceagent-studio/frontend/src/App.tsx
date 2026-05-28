import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Dashboard } from './pages/Dashboard'
import { BuilderPage } from './pages/BuilderPage'
import { CallPage } from './pages/CallPage'
import { AppointmentsPage } from './pages/AppointmentsPage'

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-950 text-white">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/build" element={<BuilderPage />} />
          <Route path="/appointments" element={<AppointmentsPage />} />
          <Route path="/call/:agentId" element={<CallPage />} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </div>
    </BrowserRouter>
  )
}

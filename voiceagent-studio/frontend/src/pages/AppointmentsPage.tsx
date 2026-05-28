import { useEffect, useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, ChevronLeft, ChevronRight, Calendar, Clock, User, Tag, X, Trash2 } from 'lucide-react'
import { appointmentApi } from '../lib/api'

interface Appointment {
  id: string
  agent_id: string
  category: string
  ref_id: string
  guest_name: string
  title: string
  appointment_date: string
  appointment_time: string | null
  details: any
  status: string
  created_at: string
}

const CATEGORY_STYLES: Record<string, { bg: string; text: string; border: string; dot: string }> = {
  hospital: { bg: 'bg-blue-900/40', text: 'text-blue-300', border: 'border-blue-800/60', dot: 'bg-blue-400' },
  restaurant: { bg: 'bg-amber-900/40', text: 'text-amber-300', border: 'border-amber-800/60', dot: 'bg-amber-400' },
  hotel: { bg: 'bg-purple-900/40', text: 'text-purple-300', border: 'border-purple-800/60', dot: 'bg-purple-400' },
}

const MONTH_NAMES = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
]

const DAY_NAMES = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

export function AppointmentsPage() {
  const navigate = useNavigate()
  const today = new Date()
  const [currentYear, setCurrentYear] = useState(today.getFullYear())
  const [currentMonth, setCurrentMonth] = useState(today.getMonth())
  const [appointments, setAppointments] = useState<Appointment[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedDate, setSelectedDate] = useState<string | null>(null)
  const [panelOpen, setPanelOpen] = useState(false)

  const monthKey = `${currentYear}-${String(currentMonth + 1).padStart(2, '0')}`

  useEffect(() => {
    setLoading(true)
    appointmentApi
      .list(monthKey)
      .then((res) => setAppointments(res.data.appointments ?? []))
      .catch(() => setAppointments([]))
      .finally(() => setLoading(false))
  }, [monthKey])

  const prevMonth = () => {
    if (currentMonth === 0) {
      setCurrentMonth(11)
      setCurrentYear((y) => y - 1)
    } else {
      setCurrentMonth((m) => m - 1)
    }
    setSelectedDate(null)
    setPanelOpen(false)
  }

  const nextMonth = () => {
    if (currentMonth === 11) {
      setCurrentMonth(0)
      setCurrentYear((y) => y + 1)
    } else {
      setCurrentMonth((m) => m + 1)
    }
    setSelectedDate(null)
    setPanelOpen(false)
  }

  // Build calendar grid
  const calendarDays = useMemo(() => {
    const firstDay = new Date(currentYear, currentMonth, 1).getDay()
    const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate()
    const daysInPrevMonth = new Date(currentYear, currentMonth, 0).getDate()

    const days: { day: number; isCurrentMonth: boolean; dateStr: string }[] = []

    // Previous month padding
    for (let i = firstDay - 1; i >= 0; i--) {
      const d = daysInPrevMonth - i
      const prevMon = currentMonth === 0 ? 12 : currentMonth
      const prevYear = currentMonth === 0 ? currentYear - 1 : currentYear
      days.push({
        day: d,
        isCurrentMonth: false,
        dateStr: `${prevYear}-${String(prevMon).padStart(2, '0')}-${String(d).padStart(2, '0')}`,
      })
    }

    // Current month days
    for (let d = 1; d <= daysInMonth; d++) {
      days.push({
        day: d,
        isCurrentMonth: true,
        dateStr: `${currentYear}-${String(currentMonth + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`,
      })
    }

    // Next month padding
    const remaining = 42 - days.length
    for (let d = 1; d <= remaining; d++) {
      const nextMon = currentMonth + 2 > 12 ? 1 : currentMonth + 2
      const nextYear = currentMonth + 2 > 12 ? currentYear + 1 : currentYear
      days.push({
        day: d,
        isCurrentMonth: false,
        dateStr: `${nextYear}-${String(nextMon).padStart(2, '0')}-${String(d).padStart(2, '0')}`,
      })
    }

    return days
  }, [currentYear, currentMonth])

  // Map date -> appointments
  const appointmentsByDate = useMemo(() => {
    const map: Record<string, Appointment[]> = {}
    for (const apt of appointments) {
      const d = apt.appointment_date
      if (!map[d]) map[d] = []
      map[d].push(apt)
    }
    return map
  }, [appointments])

  const selectedAppointments = selectedDate ? (appointmentsByDate[selectedDate] ?? []) : []

  const handleDayClick = (dateStr: string, isCurrentMonth: boolean) => {
    if (!isCurrentMonth) return
    setSelectedDate(dateStr)
    setPanelOpen(true)
  }

  const handleCancel = async (id: string) => {
    if (!confirm('Cancel this appointment?')) return
    try {
      await appointmentApi.updateStatus(id, 'cancelled')
      setAppointments((prev) =>
        prev.map((a) => (a.id === id ? { ...a, status: 'cancelled' } : a))
      )
    } catch {
      alert('Failed to cancel appointment')
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Permanently delete this appointment?')) return
    try {
      await appointmentApi.delete(id)
      setAppointments((prev) => prev.filter((a) => a.id !== id))
    } catch {
      alert('Failed to delete appointment')
    }
  }

  const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`

  const totalAppointments = appointments.filter((a) => a.status === 'confirmed').length

  return (
    <div className="max-w-6xl mx-auto px-6 py-10 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate('/')}
          className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to agents
        </button>
      </div>

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <Calendar className="w-6 h-6 text-blue-400" />
            My Appointments
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            {totalAppointments} upcoming appointment{totalAppointments !== 1 ? 's' : ''} this month
          </p>
        </div>
      </div>

      <div className={`grid ${panelOpen ? 'grid-cols-1 lg:grid-cols-3' : 'grid-cols-1'} gap-6 transition-all duration-300`}>
        {/* Calendar */}
        <div className={`${panelOpen ? 'lg:col-span-2' : ''}`}>
          <div className="bg-gray-900/60 border border-gray-800 rounded-2xl p-6 backdrop-blur-md">
            {/* Month navigation */}
            <div className="flex items-center justify-between mb-6">
              <button
                onClick={prevMonth}
                className="p-2 hover:bg-gray-800 rounded-lg transition-colors text-gray-400 hover:text-white"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>
              <h2 className="text-lg font-semibold text-white">
                {MONTH_NAMES[currentMonth]} {currentYear}
              </h2>
              <button
                onClick={nextMonth}
                className="p-2 hover:bg-gray-800 rounded-lg transition-colors text-gray-400 hover:text-white"
              >
                <ChevronRight className="w-5 h-5" />
              </button>
            </div>

            {/* Day headers */}
            <div className="grid grid-cols-7 gap-1 mb-2">
              {DAY_NAMES.map((d) => (
                <div key={d} className="text-center text-xs font-medium text-gray-500 py-2">
                  {d}
                </div>
              ))}
            </div>

            {/* Calendar grid */}
            {loading ? (
              <div className="flex items-center justify-center h-64 text-gray-500 text-sm">
                <div className="animate-pulse">Loading appointments...</div>
              </div>
            ) : (
              <div className="grid grid-cols-7 gap-1">
                {calendarDays.map((cell, idx) => {
                  const dayAppts = appointmentsByDate[cell.dateStr] ?? []
                  const confirmedAppts = dayAppts.filter((a) => a.status === 'confirmed')
                  const isToday = cell.dateStr === todayStr
                  const isSelected = cell.dateStr === selectedDate
                  const hasAppts = confirmedAppts.length > 0

                  return (
                    <button
                      key={idx}
                      onClick={() => handleDayClick(cell.dateStr, cell.isCurrentMonth)}
                      disabled={!cell.isCurrentMonth}
                      className={`relative aspect-square flex flex-col items-center justify-center rounded-xl text-sm font-medium transition-all duration-200
                        ${!cell.isCurrentMonth ? 'text-gray-700 cursor-default' : 'hover:bg-gray-800/80 cursor-pointer'}
                        ${cell.isCurrentMonth && !isSelected && !isToday ? 'text-gray-300' : ''}
                        ${isToday && !isSelected ? 'bg-blue-900/30 text-blue-300 border border-blue-800/50' : ''}
                        ${isSelected ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/20 scale-105' : ''}
                      `}
                    >
                      <span>{cell.day}</span>
                      {hasAppts && cell.isCurrentMonth && (
                        <div className="flex gap-0.5 mt-1">
                          {confirmedAppts.slice(0, 3).map((apt, i) => {
                            const style = CATEGORY_STYLES[apt.category] ?? CATEGORY_STYLES.hospital
                            return (
                              <span
                                key={i}
                                className={`w-1.5 h-1.5 rounded-full ${isSelected ? 'bg-white' : style.dot}`}
                              />
                            )
                          })}
                          {confirmedAppts.length > 3 && (
                            <span className={`text-[8px] ${isSelected ? 'text-white/80' : 'text-gray-500'}`}>
                              +{confirmedAppts.length - 3}
                            </span>
                          )}
                        </div>
                      )}
                    </button>
                  )
                })}
              </div>
            )}

            {/* Legend */}
            <div className="flex items-center gap-4 mt-4 pt-4 border-t border-gray-800">
              {Object.entries(CATEGORY_STYLES).map(([cat, style]) => (
                <div key={cat} className="flex items-center gap-1.5">
                  <span className={`w-2 h-2 rounded-full ${style.dot}`} />
                  <span className="text-xs text-gray-500 capitalize">{cat}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Side panel — selected day appointments */}
        {panelOpen && selectedDate && (
          <div className="lg:col-span-1">
            <div className="bg-gray-900/60 border border-gray-800 rounded-2xl p-5 backdrop-blur-md space-y-4 sticky top-6">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-white">
                  {new Date(selectedDate + 'T00:00:00').toLocaleDateString('en-US', {
                    weekday: 'long',
                    month: 'long',
                    day: 'numeric',
                  })}
                </h3>
                <button
                  onClick={() => { setPanelOpen(false); setSelectedDate(null) }}
                  className="p-1 text-gray-500 hover:text-white transition-colors rounded-lg hover:bg-gray-800"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {selectedAppointments.length === 0 ? (
                <div className="py-8 text-center">
                  <Calendar className="w-8 h-8 text-gray-700 mx-auto mb-2" />
                  <p className="text-sm text-gray-500">No appointments on this day</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {selectedAppointments.map((apt) => {
                    const style = CATEGORY_STYLES[apt.category] ?? CATEGORY_STYLES.hospital
                    const isCancelled = apt.status === 'cancelled'

                    return (
                      <div
                        key={apt.id}
                        className={`relative border rounded-xl p-4 space-y-3 transition-all duration-200
                          ${isCancelled
                            ? 'border-red-900/40 bg-red-950/20 opacity-60'
                            : 'border-gray-800 bg-gray-950/60 hover:border-gray-700'
                          }`}
                      >
                        {/* Category + Status */}
                        <div className="flex items-center justify-between">
                          <span className={`text-[10px] uppercase tracking-wider font-semibold px-2 py-0.5 rounded-full border ${style.bg} ${style.text} ${style.border}`}>
                            {apt.category}
                          </span>
                          <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full ${
                            isCancelled
                              ? 'bg-red-900/40 text-red-400 border border-red-800/60'
                              : 'bg-green-900/40 text-green-400 border border-green-800/60'
                          }`}>
                            {apt.status}
                          </span>
                        </div>

                        {/* Title */}
                        <p className={`text-sm font-semibold ${isCancelled ? 'text-gray-500 line-through' : 'text-white'}`}>
                          {apt.title}
                        </p>

                        {/* Details */}
                        <div className="space-y-1.5">
                          <div className="flex items-center gap-2 text-xs text-gray-400">
                            <User className="w-3 h-3" />
                            <span>{apt.guest_name}</span>
                          </div>
                          {apt.appointment_time && (
                            <div className="flex items-center gap-2 text-xs text-gray-400">
                              <Clock className="w-3 h-3" />
                              <span>{apt.appointment_time}</span>
                            </div>
                          )}
                          <div className="flex items-center gap-2 text-xs text-gray-400">
                            <Tag className="w-3 h-3" />
                            <span className="font-mono">{apt.ref_id}</span>
                          </div>
                        </div>

                        {/* Actions */}
                        {!isCancelled && (
                          <div className="flex gap-2 pt-2 border-t border-gray-800">
                            <button
                              onClick={() => handleCancel(apt.id)}
                              className="flex-1 py-1.5 text-xs font-medium text-amber-400 hover:bg-amber-900/20 border border-amber-800/40 rounded-lg transition-colors"
                            >
                              Cancel
                            </button>
                            <button
                              onClick={() => handleDelete(apt.id)}
                              className="p-1.5 text-gray-500 hover:text-red-400 hover:bg-red-900/20 rounded-lg transition-colors"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

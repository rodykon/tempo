import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Menu } from 'lucide-react'
import { api } from '../api'
import SlideMenu from '../components/SlideMenu'
import PendingSyncBadge from '../components/PendingSyncBadge'

function formatTime(seconds) {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

export default function MainScreen() {
  const [habits, setHabits]   = useState([])
  const [timings, setTimings] = useState({})
  const [menuOpen, setMenuOpen] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    async function load() {
      const [habitData, timingData] = await Promise.all([
        api.getHabits(),
        api.getTimings(),
      ])
      setHabits(habitData || [])
      const map = {}
      for (const t of (timingData || [])) map[t.habit_id] = t
      setTimings(map)
    }
    load()
  }, [])

  return (
    <div className="screen">
      <SlideMenu open={menuOpen} onClose={() => setMenuOpen(false)} />
      <header className="app-header">
        <button className="icon-btn" onClick={() => setMenuOpen(true)}><Menu size={22} /></button>
        <h1>Tempo</h1>
        <PendingSyncBadge />
      </header>
      <div className="habit-list">
        {habits.length === 0 && (
          <p className="empty-msg">No habits yet. Open the menu and go to Manage Habits to add some.</p>
        )}
        {habits.map(habit => {
          const timing    = timings[habit.id]
          const remaining = timing?.time_remaining ?? habit.time * 60
          const done      = remaining === 0
          return (
            <div
              key={habit.id}
              className={`habit-card ${done ? 'done' : 'pending'}`}
              onClick={() => navigate(`/timing/${habit.id}`)}
            >
              <div>
                <div className="habit-name">{habit.name}</div>
                <div className="habit-period">{habit.period}</div>
              </div>
              <div className="habit-time">{formatTime(remaining)}</div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

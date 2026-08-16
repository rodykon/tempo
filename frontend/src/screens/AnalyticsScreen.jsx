import { useState, useEffect } from 'react'
import { Menu } from 'lucide-react'
import { api } from '../api'
import SlideMenu from '../components/SlideMenu'
import WeeklyChart from '../components/WeeklyChart'

function formatDuration(seconds) {
  const totalMinutes = Math.round(seconds / 60)
  const h = Math.floor(totalMinutes / 60)
  const m = totalMinutes % 60
  if (h === 0) return `${m}m`
  return `${h}h ${m}m`
}

function weekLabel(periodStart) {
  const date = new Date(`${periodStart}T00:00:00Z`)
  const formatted = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', timeZone: 'UTC' })
  return `Week of ${formatted}`
}

export default function AnalyticsScreen() {
  const [menuOpen, setMenuOpen] = useState(false)
  const [data, setData] = useState(null)
  const [loadError, setLoadError] = useState(false)
  const [selectedId, setSelectedId] = useState(null)
  const [confirmOpen, setConfirmOpen] = useState(false)

  async function load() {
    try {
      const result = await api.getAnalytics()
      setData(result)
      setLoadError(false)
      setSelectedId(prev => {
        const habits = result?.habits || []
        if (habits.some(h => h.habit_id === prev)) return prev
        return habits[0]?.habit_id ?? null
      })
    } catch {
      setLoadError(true)
    }
  }

  useEffect(() => { load() }, [])

  async function handleConfirmReset() {
    setConfirmOpen(false)
    await api.resetAnalytics()
    load()
  }

  const habits = data?.habits || []
  const selected = habits.find(h => h.habit_id === selectedId) || null
  const hasData = !!(selected && selected.time_planned > 0)

  return (
    <div className="screen">
      <SlideMenu open={menuOpen} onClose={() => setMenuOpen(false)} />
      <header className="app-header">
        <button className="icon-btn" onClick={() => setMenuOpen(true)}><Menu size={22} /></button>
        <h1>Analytics</h1>
      </header>

      <div className="analytics-content">
        {loadError && <p className="empty-msg">Couldn't load analytics right now.</p>}

        {data && (
          <>
            <div className="stat-card">
              <p className="stat-label">Big Picture</p>
              <p className="stat-value">{data.overall.percentage}% of planned time completed</p>
              <p className="stat-sub">Total time completed: {formatDuration(data.overall.time_spent)}</p>
            </div>

            {habits.length === 0 ? (
              <p className="empty-msg">No habits yet.</p>
            ) : (
              <>
                <select
                  aria-label="Habit"
                  className="habit-select"
                  value={selectedId ?? ''}
                  onChange={e => setSelectedId(Number(e.target.value))}
                >
                  {habits.map(h => (
                    <option key={h.habit_id} value={h.habit_id}>{h.name}</option>
                  ))}
                </select>

                {selected && (
                  hasData ? (
                    <div className="stat-card">
                      <p className="stat-value">{selected.percentage}% of planned time completed</p>
                      <p className="stat-sub">Total time completed: {formatDuration(selected.time_spent)}</p>
                      {selected.period === 'weekly' && selected.week && (
                        <>
                          <p className="week-label">{weekLabel(selected.week.period_start)}</p>
                          <WeeklyChart week={selected.week} />
                        </>
                      )}
                    </div>
                  ) : (
                    <p className="empty-msg">No data collected yet — check back tomorrow.</p>
                  )
                )}
              </>
            )}

            <button className="danger-btn" onClick={() => setConfirmOpen(true)}>Reset Statistics</button>
          </>
        )}
      </div>

      {confirmOpen && (
        <>
          <div className="confirm-backdrop" onClick={() => setConfirmOpen(false)} />
          <div className="confirm-modal">
            <p>Are you sure? This permanently deletes all of your analytics data.</p>
            <div className="confirm-actions">
              <button type="button" className="confirm-cancel" autoFocus onClick={() => setConfirmOpen(false)}>
                Cancel
              </button>
              <button type="button" className="confirm-danger" onClick={handleConfirmReset}>
                Yes, delete
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

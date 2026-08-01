import { useState, useEffect, useRef } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Menu, ArrowLeft, Play, Pause } from 'lucide-react'
import { api } from '../api'
import SlideMenu from '../components/SlideMenu'
import PendingSyncBadge from '../components/PendingSyncBadge'

function formatTime(seconds) {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

function parseTime(str) {
  const parts = str.split(':')
  if (parts.length === 3) {
    const h = parseInt(parts[0], 10)
    const m = parseInt(parts[1], 10)
    const s = parseInt(parts[2], 10)
    if (!isNaN(h) && !isNaN(m) && !isNaN(s) && m < 60 && s < 60) return h * 3600 + m * 60 + s
  }
  if (parts.length === 2) {
    const h = parseInt(parts[0], 10)
    const m = parseInt(parts[1], 10)
    if (!isNaN(h) && !isNaN(m) && m < 60) return h * 3600 + m * 60
  }
  return null
}

export default function TimingScreen() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [habit, setHabit]               = useState(null)
  const [timeRemaining, setTimeRemaining] = useState(null)
  const [isRunning, setIsRunning]       = useState(false)
  const [editing, setEditing]           = useState(false)
  const [editValue, setEditValue]       = useState('')
  const [menuOpen, setMenuOpen]         = useState(false)
  const intervalRef  = useRef(null)
  const timeRef      = useRef(null)   // always-current value for async callbacks
  const baseRef      = useRef(null)   // { remaining, timestamp } as of the last known-good sync

  useEffect(() => { timeRef.current = timeRemaining }, [timeRemaining])

  useEffect(() => {
    async function load() {
      const [habitData, timingData] = await Promise.all([
        api.getHabits(),
        api.getTiming(id),
      ])
      const h = (habitData || []).find(h => h.id === parseInt(id))
      setHabit(h)
      if (timingData) {
        setTimeRemaining(timingData.time_remaining)
        setIsRunning(timingData.is_running)
        if (timingData.is_running) tick(timingData.time_remaining)
      }
    }
    load()
    return () => clearInterval(intervalRef.current)
  }, [id])

  // setInterval is suspended by mobile browsers while the app is backgrounded
  // or the phone sleeps, so ticks are computed from wall-clock elapsed time
  // (not decremented one-by-one) — that way the display is correct as soon
  // as ticking resumes, instead of picking up where it stalled.
  function tick(startRemaining) {
    clearInterval(intervalRef.current)
    baseRef.current = { remaining: startRemaining, timestamp: Date.now() }
    intervalRef.current = setInterval(() => {
      const elapsed = Math.floor((Date.now() - baseRef.current.timestamp) / 1000)
      const remaining = Math.max(0, baseRef.current.remaining - elapsed)
      setTimeRemaining(remaining)
      if (remaining <= 0) {
        clearInterval(intervalRef.current)
        setIsRunning(false)
        api.updateTiming(id, { time_remaining: 0, is_running: false })
      }
    }, 1000)
  }

  // Re-sync with the server whenever the app regains the foreground: a
  // suspended setInterval means the running total can be stale, and only the
  // server knows if the period rolled over while the app was backgrounded.
  useEffect(() => {
    async function resync() {
      if (document.visibilityState !== 'visible' || !isRunning) return
      const timingData = await api.getTiming(id)
      if (timingData) {
        setTimeRemaining(timingData.time_remaining)
        setIsRunning(timingData.is_running)
        if (timingData.is_running) tick(timingData.time_remaining)
        else clearInterval(intervalRef.current)
      }
    }
    document.addEventListener('visibilitychange', resync)
    return () => document.removeEventListener('visibilitychange', resync)
  }, [id, isRunning])

  async function handlePlayPause() {
    if (isRunning) {
      clearInterval(intervalRef.current)
      setIsRunning(false)
      await api.updateTiming(id, { time_remaining: timeRef.current, is_running: false })
    } else {
      await api.updateTiming(id, { time_remaining: timeRef.current, is_running: true })
      setIsRunning(true)
      tick(timeRef.current)
    }
  }

  function handleTimerClick() {
    if (!isRunning) {
      setEditValue(formatTime(timeRemaining))
      setEditing(true)
    }
  }

  function commitEdit() {
    const parsed = parseTime(editValue)
    if (parsed !== null) {
      setTimeRemaining(parsed)
      api.updateTiming(id, { time_remaining: parsed, is_running: false })
    }
    setEditing(false)
  }

  if (timeRemaining === null) return <div className="loading">Loading…</div>

  return (
    <div className="screen">
      <SlideMenu open={menuOpen} onClose={() => setMenuOpen(false)} />
      <header className="app-header">
        <button className="icon-btn" onClick={() => navigate('/')}><ArrowLeft size={22} /></button>
        <h1>{habit?.name ?? 'Habit'}</h1>
        <PendingSyncBadge />
        <button className="icon-btn" style={{ marginLeft: 'auto' }} onClick={() => setMenuOpen(true)}><Menu size={22} /></button>
      </header>
      <div className="timing-body">
        {editing ? (
          <input
            className="timer-edit-input"
            autoFocus
            value={editValue}
            onChange={e => setEditValue(e.target.value)}
            onKeyDown={e => {
              if (e.key === 'Enter')  commitEdit()
              if (e.key === 'Escape') setEditing(false)
            }}
            onBlur={commitEdit}
            placeholder="HH:MM:SS"
          />
        ) : (
          <div
            className={`timer-display ${!isRunning ? 'clickable' : ''}`}
            onClick={handleTimerClick}
            title={!isRunning ? 'Click to set time' : undefined}
          >
            {formatTime(timeRemaining)}
          </div>
        )}

        <button
          className={`play-pause-btn ${isRunning ? 'pause' : 'play'}`}
          onClick={handlePlayPause}
        >
          {isRunning ? <Pause size={28} fill="currentColor" /> : <Play size={28} fill="currentColor" />}
        </button>

        {habit && (
          <p className="habit-period-label">
            {habit.period} · {habit.time} min budget
          </p>
        )}
      </div>
    </div>
  )
}

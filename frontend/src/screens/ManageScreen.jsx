import { useState, useEffect } from 'react'
import { api } from '../api'
import SlideMenu from '../components/SlideMenu'

function minutesToHM(minutes) {
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  return `${h}:${String(m).padStart(2, '0')}`
}

function hmToMinutes(str) {
  const parts = str.split(':')
  if (parts.length === 2) {
    const h = parseInt(parts[0], 10)
    const m = parseInt(parts[1], 10)
    if (!isNaN(h) && !isNaN(m) && h >= 0 && m >= 0 && m < 60) return h * 60 + m
  }
  return null
}

const BLANK = { name: '', description: '', period: 'daily', time: '0:30' }

function HabitForm({ form, onChange, onSubmit, onCancel, submitLabel }) {
  const parts   = form.time.split(':')
  const hours   = parseInt(parts[0], 10) || 0
  const minutes = parseInt(parts[1], 10) || 0

  function update(h, m) {
    onChange({ ...form, time: `${h}:${String(m).padStart(2, '0')}` })
  }

  return (
    <form className="habit-form" onSubmit={onSubmit}>
      <input
        placeholder="Name"
        value={form.name}
        onChange={e => onChange({ ...form, name: e.target.value })}
        required
        autoFocus
      />
      <textarea
        placeholder="Description (optional)"
        value={form.description}
        onChange={e => onChange({ ...form, description: e.target.value })}
      />
      <select
        value={form.period}
        onChange={e => onChange({ ...form, period: e.target.value })}
      >
        <option value="daily">Daily</option>
        <option value="weekly">Weekly</option>
      </select>
      <div className="time-inputs">
        <div className="time-input-group">
          <input
            type="number"
            min="0"
            value={hours}
            onChange={e => update(Math.max(0, parseInt(e.target.value) || 0), minutes)}
          />
          <label>hours</label>
        </div>
        <span className="time-colon">:</span>
        <div className="time-input-group">
          <input
            type="number"
            min="0"
            max="59"
            value={minutes}
            onChange={e => update(hours, Math.min(59, Math.max(0, parseInt(e.target.value) || 0)))}
          />
          <label>minutes</label>
        </div>
      </div>
      <div className="form-actions">
        <button type="submit">{submitLabel}</button>
        <button type="button" onClick={onCancel}>Cancel</button>
      </div>
    </form>
  )
}

export default function ManageScreen() {
  const [habits, setHabits]       = useState([])
  const [menuOpen, setMenuOpen]   = useState(false)
  const [editingId, setEditingId] = useState(null)
  const [editForm, setEditForm]   = useState(BLANK)
  const [showCreate, setShowCreate] = useState(false)
  const [createForm, setCreateForm] = useState(BLANK)

  async function load() {
    const data = await api.getHabits()
    setHabits(data || [])
  }

  useEffect(() => { load() }, [])

  function startEdit(habit) {
    setEditingId(habit.id)
    setEditForm({ name: habit.name, description: habit.description, period: habit.period, time: minutesToHM(habit.time) })
    setShowCreate(false)
  }

  async function handleSave(e) {
    e.preventDefault()
    await api.updateHabit(editingId, { ...editForm, time: hmToMinutes(editForm.time) })
    setEditingId(null)
    load()
  }

  async function handleDelete(id) {
    if (!confirm('Delete this habit?')) return
    await api.deleteHabit(id)
    load()
  }

  async function handleCreate(e) {
    e.preventDefault()
    await api.createHabit({ ...createForm, time: hmToMinutes(createForm.time) })
    setShowCreate(false)
    setCreateForm(BLANK)
    load()
  }

  const daily  = habits.filter(h => h.period === 'daily')
  const weekly = habits.filter(h => h.period === 'weekly')

  function HabitItem({ habit }) {
    const isEditing = editingId === habit.id
    return (
      <div className="manage-habit-item">
        {isEditing ? (
          <HabitForm
            form={editForm}
            onChange={setEditForm}
            onSubmit={handleSave}
            onCancel={() => setEditingId(null)}
            submitLabel="Save"
          />
        ) : (
          <div className="manage-habit-row" onClick={() => startEdit(habit)}>
            <div className="manage-habit-info">
              <span className="manage-habit-name">{habit.name}</span>
              {habit.description && (
                <span className="manage-habit-desc">{habit.description}</span>
              )}
              <span className="manage-habit-meta">{minutesToHM(habit.time)} / {habit.period}</span>
            </div>
            <button
              className="delete-btn"
              onClick={e => { e.stopPropagation(); handleDelete(habit.id) }}
            >
              ✕
            </button>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="screen">
      <SlideMenu open={menuOpen} onClose={() => setMenuOpen(false)} />
      <header className="app-header">
        <button className="icon-btn" onClick={() => setMenuOpen(true)}>☰</button>
        <h1>Manage Habits</h1>
      </header>

      <div className="manage-content">
        {habits.length === 0 && (
          <p className="empty-msg">No habits yet. Tap + to add your first one.</p>
        )}
        {daily.length > 0 && (
          <section>
            <p className="section-title">Daily</p>
            {daily.map(h => <HabitItem key={h.id} habit={h} />)}
          </section>
        )}
        {weekly.length > 0 && (
          <section>
            <p className="section-title">Weekly</p>
            {weekly.map(h => <HabitItem key={h.id} habit={h} />)}
          </section>
        )}
      </div>

      {showCreate && (
        <div className="create-overlay" onClick={e => { if (e.target === e.currentTarget) setShowCreate(false) }}>
          <div className="create-card">
            <h2>New Habit</h2>
            <HabitForm
              form={createForm}
              onChange={setCreateForm}
              onSubmit={handleCreate}
              onCancel={() => setShowCreate(false)}
              submitLabel="Create"
            />
          </div>
        </div>
      )}

      <button
        className="fab"
        onClick={() => { setCreateForm(BLANK); setEditingId(null); setShowCreate(true) }}
      >
        +
      </button>
    </div>
  )
}

import { useState } from 'react'
import SlideMenu from '../components/SlideMenu'

export default function AboutScreen() {
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <div className="screen">
      <SlideMenu open={menuOpen} onClose={() => setMenuOpen(false)} />
      <header className="app-header">
        <button className="icon-btn" onClick={() => setMenuOpen(true)}>☰</button>
        <h1>About</h1>
      </header>
      <div className="about-content">
        <h2>Tempo <span style={{ fontSize: '1rem', color: 'var(--muted)', fontWeight: 400 }}>v0.1.0</span></h2>
        <p>
          Tempo is a time-management app built on a simple idea: assign each habit a time budget
          per period (daily or weekly), then track whether you actually spend that time.
          Unspent time does not carry over — every period starts fresh.
        </p>
        <h3>How it works</h3>
        <ol>
          <li>Add habits in <em>Manage Habits</em> and set a time budget for each.</li>
          <li>On the main screen, tap a habit to open its timer.</li>
          <li>Press play when you start, pause when you stop.</li>
          <li>Habits turn green once you've used their full allocation for the period.</li>
          <li>Timers reset automatically at the start of each new period.</li>
        </ol>
      </div>
    </div>
  )
}

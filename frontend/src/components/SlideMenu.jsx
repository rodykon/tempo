import { useNavigate } from 'react-router-dom'
import { clearTokens } from '../api'

export default function SlideMenu({ open, onClose }) {
  const navigate = useNavigate()

  function go(path) {
    onClose()
    navigate(path)
  }

  function signOut() {
    clearTokens()
    navigate('/login')
  }

  return (
    <>
      {open && <div className="menu-backdrop" onClick={onClose} />}
      <nav className={`slide-menu ${open ? 'open' : ''}`}>
        <div className="menu-header">Tempo</div>
        <button onClick={() => go('/')}>Main</button>
        <button onClick={() => go('/manage')}>Manage Habits</button>
        <button onClick={() => go('/analytics')}>Analytics</button>
        <button onClick={() => go('/about')}>About</button>
        <button className="menu-signout" onClick={signOut}>Sign out</button>
      </nav>
    </>
  )
}

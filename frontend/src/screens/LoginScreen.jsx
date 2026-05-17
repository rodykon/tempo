import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, setToken } from '../api'

export default function LoginScreen() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError]       = useState('')
  const navigate = useNavigate()

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    try {
      const data = await api.login(username, password)
      if (data?.access) {
        setToken(data.access)
        navigate('/')
      } else {
        setError('Invalid credentials.')
      }
    } catch {
      setError('Login failed. Check your username and password.')
    }
  }

  return (
    <div className="login-screen">
      <div className="login-card">
        <h1>Tempo</h1>
        <p>Time management, simplified.</p>
        <form onSubmit={handleSubmit}>
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={e => setUsername(e.target.value)}
            required
            autoFocus
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            required
          />
          {error && <p className="error">{error}</p>}
          <button type="submit">Sign In</button>
        </form>
      </div>
    </div>
  )
}

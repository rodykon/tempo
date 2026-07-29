import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { getToken } from './api'
import LoginScreen from './screens/LoginScreen'
import MainScreen from './screens/MainScreen'
import TimingScreen from './screens/TimingScreen'
import ManageScreen from './screens/ManageScreen'
import AboutScreen from './screens/AboutScreen'
import UpdatePrompt from './components/UpdatePrompt'

function RequireAuth({ children }) {
  return getToken() ? children : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <BrowserRouter>
      <UpdatePrompt />
      <Routes>
        <Route path="/login" element={<LoginScreen />} />
        <Route path="/" element={<RequireAuth><MainScreen /></RequireAuth>} />
        <Route path="/timing/:id" element={<RequireAuth><TimingScreen /></RequireAuth>} />
        <Route path="/manage" element={<RequireAuth><ManageScreen /></RequireAuth>} />
        <Route path="/about" element={<RequireAuth><AboutScreen /></RequireAuth>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

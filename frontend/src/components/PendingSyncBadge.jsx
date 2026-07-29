import { useState, useEffect } from 'react'
import { CloudOff } from 'lucide-react'
import { getPendingCount } from '../api'

export default function PendingSyncBadge() {
  const [count, setCount] = useState(getPendingCount())

  useEffect(() => {
    const update = () => setCount(getPendingCount())
    window.addEventListener('tempo:pending-sync-changed', update)
    window.addEventListener('online', update)
    window.addEventListener('offline', update)
    return () => {
      window.removeEventListener('tempo:pending-sync-changed', update)
      window.removeEventListener('online', update)
      window.removeEventListener('offline', update)
    }
  }, [])

  if (count === 0) return null

  return (
    <span className="pending-sync-badge" title="Changes waiting to sync">
      <CloudOff size={13} />
      {count}
    </span>
  )
}

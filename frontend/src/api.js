const BASE = '/api'

const PENDING_KEY = 'tempo_pending_timing'
const CACHE_HABITS_KEY = 'tempo_cache_habits'
const CACHE_TIMINGS_KEY = 'tempo_cache_timings'
const CACHE_TIMING_PREFIX = 'tempo_cache_timing_'
const PERIOD_STARTS_KEY = 'tempo_period_starts'

class NetworkError extends Error {}

function readJSON(key, fallback) {
  try {
    const raw = localStorage.getItem(key)
    return raw ? JSON.parse(raw) : fallback
  } catch {
    return fallback
  }
}

function writeJSON(key, value) {
  localStorage.setItem(key, JSON.stringify(value))
}

// ---- auth tokens ----

export function getToken() {
  return localStorage.getItem('access_token')
}

function getRefreshToken() {
  return localStorage.getItem('refresh_token')
}

export function setTokens(access, refresh) {
  localStorage.setItem('access_token', access)
  if (refresh) localStorage.setItem('refresh_token', refresh)
}

export function clearTokens() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
}

// ---- period_start bookkeeping (needed so queued/offline writes can be
// rejected server-side if the period rolled over while disconnected) ----

function rememberPeriodStart(habitId, periodStart) {
  if (!periodStart) return
  const map = readJSON(PERIOD_STARTS_KEY, {})
  map[habitId] = periodStart
  writeJSON(PERIOD_STARTS_KEY, map)
}

function getRememberedPeriodStart(habitId) {
  return readJSON(PERIOD_STARTS_KEY, {})[habitId]
}

// Reflects a local timing write into the read-cache immediately, so an
// offline reload shows what the user just set rather than the last
// server-confirmed value (which may predate this write).
function updateCachedTiming(habitId, { time_remaining, is_running }) {
  const key = `${CACHE_TIMING_PREFIX}${habitId}`
  const existing = readJSON(key, null)
  if (existing) writeJSON(key, { ...existing, time_remaining, is_running })

  const list = readJSON(CACHE_TIMINGS_KEY, null)
  if (list) {
    const idx = list.findIndex((t) => String(t.habit_id) === String(habitId))
    if (idx !== -1) {
      list[idx] = { ...list[idx], time_remaining, is_running }
      writeJSON(CACHE_TIMINGS_KEY, list)
    }
  }
}

// ---- offline write queue for timing updates ----

export function getPendingTimingUpdates() {
  return readJSON(PENDING_KEY, {})
}

export function getPendingCount() {
  return Object.keys(getPendingTimingUpdates()).length
}

function notifyPendingChanged() {
  window.dispatchEvent(new Event('tempo:pending-sync-changed'))
}

function queueTimingUpdate(habitId, payload) {
  const queue = getPendingTimingUpdates()
  queue[habitId] = payload
  writeJSON(PENDING_KEY, queue)
  notifyPendingChanged()
}

function unqueueTimingUpdate(habitId) {
  const queue = getPendingTimingUpdates()
  if (habitId in queue) {
    delete queue[habitId]
    writeJSON(PENDING_KEY, queue)
    notifyPendingChanged()
  }
}

let flushing = false
export async function flushPendingTimingUpdates() {
  if (flushing) return
  flushing = true
  try {
    const queue = getPendingTimingUpdates()
    for (const habitId of Object.keys(queue)) {
      try {
        await rawRequest('PUT', `/timing/${habitId}/`, queue[habitId])
        unqueueTimingUpdate(habitId)
      } catch (err) {
        if (err instanceof NetworkError) break // still offline, try again next trigger
        unqueueTimingUpdate(habitId) // permanently invalid (e.g. wrong user) — drop it
      }
    }
  } finally {
    flushing = false
  }
}

if (typeof window !== 'undefined') {
  window.addEventListener('online', () => { flushPendingTimingUpdates() })
  if (navigator.onLine) flushPendingTimingUpdates()
}

// ---- core request machinery ----

async function refreshAccessToken() {
  const refresh = getRefreshToken()
  if (!refresh) throw new Error('no-refresh-token')

  let res
  try {
    res = await fetch(`${BASE}/auth/token/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh }),
    })
  } catch {
    throw new NetworkError('offline during token refresh')
  }

  if (!res.ok) throw new Error('refresh-rejected')
  const data = await res.json()
  setTokens(data.access, data.refresh)
  return data.access
}

async function rawRequest(method, path, body = null, _retried = false) {
  const headers = { 'Content-Type': 'application/json' }
  const token = getToken()
  if (token) headers['Authorization'] = `Bearer ${token}`

  let res
  try {
    res = await fetch(`${BASE}${path}`, {
      method,
      headers,
      body: body != null ? JSON.stringify(body) : undefined,
    })
  } catch {
    throw new NetworkError(`network error: ${method} ${path}`)
  }

  // Only authenticated requests are eligible for silent refresh-and-retry —
  // this excludes the login call itself, which never attaches a token.
  if (res.status === 401 && token && !_retried) {
    try {
      await refreshAccessToken()
    } catch (err) {
      if (err instanceof NetworkError) throw err
      clearTokens()
      window.location.href = '/login'
      return null
    }
    return rawRequest(method, path, body, true)
  }

  if (res.status === 401) {
    clearTokens()
    window.location.href = '/login'
    return null
  }

  if (res.status === 204) return null

  const data = await res.json()
  if (!res.ok) throw data
  return data
}

const request = rawRequest

export const api = {
  login: async (username, password) => {
    const data = await request('POST', '/auth/token/', { username, password })
    if (data?.access) flushPendingTimingUpdates()
    return data
  },

  getHabits: async () => {
    try {
      const data = await request('GET', '/habits/')
      writeJSON(CACHE_HABITS_KEY, data)
      return data
    } catch (err) {
      if (err instanceof NetworkError) return readJSON(CACHE_HABITS_KEY, [])
      throw err
    }
  },

  createHabit: (data) => request('POST', '/habits/', data),
  updateHabit: (id, data) => request('PATCH', `/habits/${id}/`, data),
  deleteHabit: (id) => request('DELETE', `/habits/${id}/`),

  getTimings: async () => {
    try {
      const data = await request('GET', '/timing/')
      writeJSON(CACHE_TIMINGS_KEY, data)
      for (const t of data) rememberPeriodStart(t.habit_id, t.period_start)
      return data
    } catch (err) {
      if (err instanceof NetworkError) return readJSON(CACHE_TIMINGS_KEY, [])
      throw err
    }
  },

  getTiming: async (id) => {
    try {
      const data = await request('GET', `/timing/${id}/`)
      rememberPeriodStart(id, data.period_start)
      writeJSON(`${CACHE_TIMING_PREFIX}${id}`, data)
      return data
    } catch (err) {
      if (err instanceof NetworkError) return readJSON(`${CACHE_TIMING_PREFIX}${id}`, null)
      throw err
    }
  },

  updateTiming: async (id, data) => {
    const periodStart = getRememberedPeriodStart(id)
    const payload = periodStart ? { ...data, period_start: periodStart } : data
    updateCachedTiming(id, data) // keep the offline read-cache in sync with local intent
    try {
      const result = await request('PUT', `/timing/${id}/`, payload)
      unqueueTimingUpdate(id)
      return result
    } catch (err) {
      if (err instanceof NetworkError) {
        queueTimingUpdate(id, payload)
        return null
      }
      throw err
    }
  },

  getAnalytics: () => request('GET', '/analytics/'),
  resetAnalytics: () => request('DELETE', '/analytics/'),
}

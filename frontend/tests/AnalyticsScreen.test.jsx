import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'

vi.mock('../src/api', () => ({
  api: {
    getAnalytics: vi.fn(),
    resetAnalytics: vi.fn(),
  },
  getToken: vi.fn(),
  setTokens: vi.fn(),
  clearTokens: vi.fn(),
}))

import AnalyticsScreen from '../src/screens/AnalyticsScreen'
import { api } from '../src/api'

const DATA = {
  overall: { time_planned: 5400, time_spent: 2700, percentage: 50.0 },
  habits: [
    {
      habit_id: 1,
      name: 'Read',
      period: 'daily',
      time_planned: 1800,
      time_spent: 900,
      percentage: 33.3,
      week: null,
    },
    {
      habit_id: 2,
      name: 'Exercise',
      period: 'weekly',
      time_planned: 3600,
      time_spent: 1800,
      percentage: 66.7,
      week: {
        period_start: '2026-06-14',
        days: [
          { date: '2026-06-14', weekday: 'Sun', time_spent: 0 },
          { date: '2026-06-15', weekday: 'Mon', time_spent: 600 },
          { date: '2026-06-16', weekday: 'Tue', time_spent: 1200 },
          { date: '2026-06-17', weekday: 'Wed', time_spent: 0 },
          { date: '2026-06-18', weekday: 'Thu', time_spent: 0 },
          { date: '2026-06-19', weekday: 'Fri', time_spent: 0 },
          { date: '2026-06-20', weekday: 'Sat', time_spent: 0 },
        ],
      },
    },
  ],
}

async function renderScreen() {
  const user = userEvent.setup()
  render(
    <MemoryRouter>
      <AnalyticsScreen />
    </MemoryRouter>
  )
  await screen.findByText('Big Picture')
  return user
}

beforeEach(() => {
  vi.clearAllMocks()
  api.getAnalytics.mockResolvedValue(DATA)
  api.resetAnalytics.mockResolvedValue(null)
})

describe('AnalyticsScreen', () => {
  it('renders the Big Picture percentage and total completed', async () => {
    await renderScreen()
    expect(screen.getByText('50% of planned time completed')).toBeTruthy()
    expect(screen.getByText('Total time completed: 45m')).toBeTruthy()
  })

  it('defaults to the first habit and shows its stats', async () => {
    await renderScreen()
    expect(screen.getByRole('combobox').value).toBe('1')
    expect(screen.getByText('33.3% of planned time completed')).toBeTruthy()
    expect(screen.getByText('Total time completed: 15m')).toBeTruthy()
  })

  it('changing the habit dropdown swaps to the second habit\'s numbers', async () => {
    const user = await renderScreen()
    await user.selectOptions(screen.getByRole('combobox'), '2')
    expect(screen.getByText('66.7% of planned time completed')).toBeTruthy()
    expect(screen.getByText('Total time completed: 30m')).toBeTruthy()
  })

  it('renders the weekly chart only for a weekly habit', async () => {
    const user = await renderScreen()

    // Daily habit selected by default -- no chart.
    expect(screen.queryByRole('img')).toBeNull()

    await user.selectOptions(screen.getByRole('combobox'), '2')

    const chart = screen.getByRole('img')
    expect(chart).toBeTruthy()
    const summaryItems = screen.getAllByText(/^(Sun|Mon|Tue|Wed|Thu|Fri|Sat) /)
    expect(summaryItems.length).toBe(7)
    expect(screen.getByText('Mon 10m')).toBeTruthy()
    expect(screen.getByText('Tue 20m')).toBeTruthy()
    expect(screen.getByText('Sun 0m')).toBeTruthy()
  })

  it('requires confirmation before resetting', async () => {
    const user = await renderScreen()

    await user.click(screen.getByText('Reset Statistics'))
    expect(api.resetAnalytics).not.toHaveBeenCalled()
    expect(screen.getByText(/Are you sure/)).toBeTruthy()

    await user.click(screen.getByText('Cancel'))
    expect(api.resetAnalytics).not.toHaveBeenCalled()
    expect(screen.queryByText(/Are you sure/)).toBeNull()

    await user.click(screen.getByText('Reset Statistics'))
    await user.click(screen.getByText('Yes, delete'))
    expect(api.resetAnalytics).toHaveBeenCalledTimes(1)
    expect(api.getAnalytics).toHaveBeenCalledTimes(2) // initial load + refetch after reset
  })

  it('shows guidance and a safe reset button when there are no habits', async () => {
    api.getAnalytics.mockResolvedValue({ overall: { time_planned: 0, time_spent: 0, percentage: 0.0 }, habits: [] })
    const user = await renderScreen()

    expect(screen.getByText('No habits yet.')).toBeTruthy()
    expect(screen.queryByRole('combobox')).toBeNull()

    await user.click(screen.getByText('Reset Statistics'))
    expect(screen.getByText(/Are you sure/)).toBeTruthy()
  })
})

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'

vi.mock('../src/api', () => ({
  api: {
    getHabits: vi.fn(),
    createHabit: vi.fn(),
    updateHabit: vi.fn(),
    deleteHabit: vi.fn(),
  },
  getToken: vi.fn(),
  setTokens: vi.fn(),
  clearTokens: vi.fn(),
}))

import ManageScreen from '../src/screens/ManageScreen'
import { api } from '../src/api'

const HABIT = {
  id: 1,
  name: 'Reading',
  description: 'Books',
  period: 'daily',
  time: 30,
}

async function renderScreen() {
  const user = userEvent.setup()
  render(
    <MemoryRouter>
      <ManageScreen />
    </MemoryRouter>
  )
  await screen.findByText('Reading')
  return user
}

async function openEditForm(user) {
  await user.click(screen.getByText('Reading'))
  return screen.getByPlaceholderText('Name').closest('form')
}

beforeEach(() => {
  vi.clearAllMocks()
  api.getHabits.mockResolvedValue([HABIT])
  api.updateHabit.mockResolvedValue({ ...HABIT })
  api.createHabit.mockResolvedValue({ ...HABIT, id: 2 })
})

describe('ManageScreen edit form focus', () => {
  it('keeps focus in the description field while editing', async () => {
    const user = await renderScreen()
    await openEditForm(user)

    const description = screen.getByPlaceholderText('Description (optional)')
    await user.click(description)
    await user.type(description, ' daily')

    expect(document.activeElement).toBe(description)
    expect(description.value).toBe('Books daily')
    expect(screen.getByPlaceholderText('Name').value).toBe('Reading')
  })

  it('keeps focus in the hours field while editing', async () => {
    const user = await renderScreen()
    const form = await openEditForm(user)

    const [hours] = within(form).getAllByRole('spinbutton')
    await user.click(hours)
    await user.clear(hours)
    await user.type(hours, '2')

    expect(document.activeElement).toBe(within(form).getAllByRole('spinbutton')[0])
    expect(within(form).getAllByRole('spinbutton')[0].value).toBe('2')
    expect(screen.getByPlaceholderText('Name').value).toBe('Reading')
  })

  it('keeps focus in the minutes field while editing', async () => {
    const user = await renderScreen()
    const form = await openEditForm(user)

    const minutes = within(form).getAllByRole('spinbutton')[1]
    await user.click(minutes)
    await user.clear(minutes)
    await user.type(minutes, '45')

    expect(document.activeElement).toBe(within(form).getAllByRole('spinbutton')[1])
    expect(within(form).getAllByRole('spinbutton')[1].value).toBe('45')
  })

  it('does not steal focus to the name field when the period changes', async () => {
    const user = await renderScreen()
    const form = await openEditForm(user)

    const period = within(form).getByRole('combobox')
    await user.selectOptions(period, 'weekly')

    expect(document.activeElement).not.toBe(screen.getByPlaceholderText('Name'))
    expect(document.activeElement).toBe(period)
    expect(within(form).getByRole('combobox')).toBe(period)
    expect(period.value).toBe('weekly')
  })

  it('does not remount the edit form inputs on every keystroke', async () => {
    const user = await renderScreen()
    await openEditForm(user)

    const name = screen.getByPlaceholderText('Name')
    const description = screen.getByPlaceholderText('Description (optional)')

    await user.type(name, '!')
    await user.type(description, '!')

    expect(screen.getByPlaceholderText('Name')).toBe(name)
    expect(screen.getByPlaceholderText('Description (optional)')).toBe(description)
    expect(name.value).toBe('Reading!')
    expect(description.value).toBe('Books!')
  })

  it('saves the edited values', async () => {
    const user = await renderScreen()
    const form = await openEditForm(user)

    const name = screen.getByPlaceholderText('Name')
    await user.clear(name)
    await user.type(name, 'Reading more')

    const minutes = within(form).getAllByRole('spinbutton')[1]
    await user.clear(minutes)
    await user.type(minutes, '45')

    await user.click(screen.getByRole('button', { name: 'Save' }))

    expect(api.updateHabit).toHaveBeenCalledWith(1, {
      name: 'Reading more',
      description: 'Books',
      period: 'daily',
      time: 45,
    })
  })
})

describe('ManageScreen create form focus', () => {
  it('keeps focus in the description field while creating', async () => {
    const user = await renderScreen()
    await user.click(document.querySelector('.fab'))

    const description = screen.getByPlaceholderText('Description (optional)')
    await user.click(description)
    await user.type(description, 'New notes')

    expect(document.activeElement).toBe(description)
    expect(description.value).toBe('New notes')
    expect(screen.getByPlaceholderText('Name').value).toBe('')
  })
})

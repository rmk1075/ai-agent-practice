import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { vi } from 'vitest'
import Header from './Header'

describe('Header', () => {
  it('renders the app title', () => {
    render(
      <MemoryRouter>
        <Header onToggleSidebar={vi.fn()} />
      </MemoryRouter>
    )
    expect(screen.getByText('AI 계약 어시스턴트')).toBeInTheDocument()
  })

  it('calls onToggleSidebar when hamburger is clicked', () => {
    const onToggleSidebar = vi.fn()
    render(
      <MemoryRouter>
        <Header onToggleSidebar={onToggleSidebar} />
      </MemoryRouter>
    )
    fireEvent.click(screen.getByRole('button', { name: /menu/i }))
    expect(onToggleSidebar).toHaveBeenCalledTimes(1)
  })
})

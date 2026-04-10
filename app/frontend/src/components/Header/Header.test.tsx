import { render, screen, fireEvent } from '@testing-library/react'
import { vi } from 'vitest'
import Header from './Header'

describe('Header', () => {
  it('renders the app title', () => {
    render(<Header onToggleSidebar={vi.fn()} />)
    expect(screen.getByText('AI 계약 어시스턴트')).toBeInTheDocument()
  })

  it('calls onToggleSidebar when hamburger is clicked', () => {
    const onToggleSidebar = vi.fn()
    render(<Header onToggleSidebar={onToggleSidebar} />)
    fireEvent.click(screen.getByRole('button', { name: /menu/i }))
    expect(onToggleSidebar).toHaveBeenCalledTimes(1)
  })
})

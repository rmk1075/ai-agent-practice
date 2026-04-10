import { render, screen, fireEvent } from '@testing-library/react'
import { vi } from 'vitest'
import Sidebar from './Sidebar'
import type { Conversation } from '../../api/conversations'

const mockConversations: Conversation[] = [
  { id: 1, name: 'Conv 1', created_at: '', updated_at: '' },
  { id: 2, name: 'Conv 2', created_at: '', updated_at: '' },
]

const defaultProps = {
  isOpen: true,
  conversations: mockConversations,
  selectedId: null,
  onSelect: vi.fn(),
  onDelete: vi.fn(),
  onNewConversation: vi.fn(),
  onClose: vi.fn(),
}

describe('Sidebar', () => {
  it('renders conversation names when open', () => {
    render(<Sidebar {...defaultProps} />)
    expect(screen.getByText('Conv 1')).toBeInTheDocument()
    expect(screen.getByText('Conv 2')).toBeInTheDocument()
  })

  it('calls onSelect when a conversation is clicked', () => {
    const onSelect = vi.fn()
    render(<Sidebar {...defaultProps} onSelect={onSelect} />)
    fireEvent.click(screen.getByText('Conv 1'))
    expect(onSelect).toHaveBeenCalledWith(mockConversations[0])
  })

  it('calls onClose when overlay is clicked', () => {
    const onClose = vi.fn()
    render(<Sidebar {...defaultProps} onClose={onClose} />)
    fireEvent.click(screen.getByTestId('sidebar-overlay'))
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('calls onNewConversation when New Conversation button is clicked', () => {
    const onNewConversation = vi.fn()
    render(<Sidebar {...defaultProps} conversations={[]} onNewConversation={onNewConversation} />)
    fireEvent.click(screen.getByRole('button', { name: /new conversation/i }))
    expect(onNewConversation).toHaveBeenCalledTimes(1)
  })

  it('renders nothing when isOpen is false', () => {
    render(<Sidebar {...defaultProps} isOpen={false} />)
    expect(screen.queryByTestId('sidebar-overlay')).not.toBeInTheDocument()
  })
})

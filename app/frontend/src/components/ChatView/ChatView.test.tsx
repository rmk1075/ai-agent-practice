import { render, screen } from '@testing-library/react'
import { vi } from 'vitest'
import ChatView from './ChatView'
import type { Message } from '../../api/conversations'

const messages: Message[] = [
  { id: 1, role: 'user', content: 'Hello', created_at: '' },
  { id: 2, role: 'assistant', content: 'Hi there', created_at: '' },
]

describe('ChatView', () => {
  it('renders all messages', () => {
    render(<ChatView messages={messages} onSend={vi.fn()} isStreaming={false} />)
    expect(screen.getByText('Hello')).toBeInTheDocument()
    expect(screen.getByText('Hi there')).toBeInTheDocument()
  })

  it('renders the message input', () => {
    render(<ChatView messages={messages} onSend={vi.fn()} isStreaming={false} />)
    expect(screen.getByRole('textbox')).toBeInTheDocument()
  })
})

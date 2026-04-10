import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import MessageInput from './MessageInput'

describe('MessageInput', () => {
  it('renders textarea with placeholder', () => {
    render(<MessageInput onSend={vi.fn()} disabled={false} />)
    expect(
      screen.getByPlaceholderText(
        '계약 상황을 편하게 말씀해 주세요. AI가 내용을 분석해 가장 적합한 표준계약서를 추천해 드립니다.'
      )
    ).toBeInTheDocument()
  })

  it('calls onSend with trimmed input value when send button is clicked', async () => {
    const onSend = vi.fn()
    render(<MessageInput onSend={onSend} disabled={false} />)
    await userEvent.type(screen.getByRole('textbox'), 'hello')
    fireEvent.click(screen.getByRole('button', { name: /send/i }))
    expect(onSend).toHaveBeenCalledWith('hello')
  })

  it('clears input after send', async () => {
    render(<MessageInput onSend={vi.fn()} disabled={false} />)
    const textarea = screen.getByRole('textbox')
    await userEvent.type(textarea, 'hello')
    fireEvent.click(screen.getByRole('button', { name: /send/i }))
    expect(textarea).toHaveValue('')
  })

  it('calls onSend when Enter is pressed without Shift', async () => {
    const onSend = vi.fn()
    render(<MessageInput onSend={onSend} disabled={false} />)
    await userEvent.type(screen.getByRole('textbox'), 'hello')
    await userEvent.keyboard('{Enter}')
    expect(onSend).toHaveBeenCalledWith('hello')
  })

  it('does not call onSend on Shift+Enter', async () => {
    const onSend = vi.fn()
    render(<MessageInput onSend={onSend} disabled={false} />)
    await userEvent.type(screen.getByRole('textbox'), 'hello')
    await userEvent.keyboard('{Shift>}{Enter}{/Shift}')
    expect(onSend).not.toHaveBeenCalled()
  })

  it('disables send button when disabled is true', () => {
    render(<MessageInput onSend={vi.fn()} disabled={true} />)
    expect(screen.getByRole('button', { name: /send/i })).toBeDisabled()
  })

  it('does not call onSend with empty input', () => {
    const onSend = vi.fn()
    render(<MessageInput onSend={onSend} disabled={false} />)
    fireEvent.click(screen.getByRole('button', { name: /send/i }))
    expect(onSend).not.toHaveBeenCalled()
  })
})

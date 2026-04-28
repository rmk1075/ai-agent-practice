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

  it('calls onSend with trimmed input value and undefined file when send button is clicked', async () => {
    const onSend = vi.fn()
    render(<MessageInput onSend={onSend} disabled={false} />)
    await userEvent.type(screen.getByRole('textbox'), 'hello')
    fireEvent.click(screen.getByRole('button', { name: /send/i }))
    expect(onSend).toHaveBeenCalledWith('hello', undefined)
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
    expect(onSend).toHaveBeenCalledWith('hello', undefined)
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

  it('does not call onSend with whitespace-only input', async () => {
    const onSend = vi.fn()
    render(<MessageInput onSend={onSend} disabled={false} />)
    await userEvent.type(screen.getByRole('textbox'), '   ')
    fireEvent.click(screen.getByRole('button', { name: /send/i }))
    expect(onSend).not.toHaveBeenCalled()
  })

  it('disables textarea and button when disabled prop is true', async () => {
    const onSend = vi.fn()
    render(<MessageInput onSend={onSend} disabled={true} />)
    expect(screen.getByRole('textbox')).toBeDisabled()
    expect(screen.getByRole('button', { name: /send/i })).toBeDisabled()
  })

  describe('file attachment', () => {
    it('renders a hidden file input accepting .pdf and .docx', () => {
      render(<MessageInput onSend={vi.fn()} disabled={false} />)
      const input = document.querySelector('input[type="file"]') as HTMLInputElement
      expect(input).not.toBeNull()
      expect(input.accept).toContain('.pdf')
      expect(input.accept).toContain('.docx')
    })

    it('shows file badge after file is selected', async () => {
      render(<MessageInput onSend={vi.fn()} disabled={false} />)
      const input = document.querySelector('input[type="file"]') as HTMLInputElement
      const file = new File(['content'], 'contract.pdf', { type: 'application/pdf' })
      await userEvent.upload(input, file)
      expect(screen.getByText(/contract\.pdf/)).toBeInTheDocument()
    })

    it('clears file badge when remove button is clicked', async () => {
      render(<MessageInput onSend={vi.fn()} disabled={false} />)
      const input = document.querySelector('input[type="file"]') as HTMLInputElement
      const file = new File(['content'], 'contract.pdf', { type: 'application/pdf' })
      await userEvent.upload(input, file)
      fireEvent.click(screen.getByRole('button', { name: /파일 제거/i }))
      expect(screen.queryByText('contract.pdf')).not.toBeInTheDocument()
    })

    it('calls onSend with empty string and file when only file is provided', async () => {
      const onSend = vi.fn()
      render(<MessageInput onSend={onSend} disabled={false} />)
      const input = document.querySelector('input[type="file"]') as HTMLInputElement
      const file = new File(['content'], 'contract.pdf', { type: 'application/pdf' })
      await userEvent.upload(input, file)
      fireEvent.click(screen.getByRole('button', { name: /send/i }))
      expect(onSend).toHaveBeenCalledWith('', file)
    })

    it('calls onSend with content and file when both are provided', async () => {
      const onSend = vi.fn()
      render(<MessageInput onSend={onSend} disabled={false} />)
      const input = document.querySelector('input[type="file"]') as HTMLInputElement
      const file = new File(['content'], 'contract.pdf', { type: 'application/pdf' })
      await userEvent.upload(input, file)
      await userEvent.type(screen.getByRole('textbox'), 'hello')
      fireEvent.click(screen.getByRole('button', { name: /send/i }))
      expect(onSend).toHaveBeenCalledWith('hello', file)
    })

    it('does not call onSend when both content and file are empty', () => {
      const onSend = vi.fn()
      render(<MessageInput onSend={onSend} disabled={false} />)
      fireEvent.click(screen.getByRole('button', { name: /send/i }))
      expect(onSend).not.toHaveBeenCalled()
    })

    it('clears file badge after send', async () => {
      render(<MessageInput onSend={vi.fn()} disabled={false} />)
      const input = document.querySelector('input[type="file"]') as HTMLInputElement
      const file = new File(['content'], 'contract.pdf', { type: 'application/pdf' })
      await userEvent.upload(input, file)
      fireEvent.click(screen.getByRole('button', { name: /send/i }))
      expect(screen.queryByText('contract.pdf')).not.toBeInTheDocument()
    })

    it('displays externalError message', () => {
      render(<MessageInput onSend={vi.fn()} disabled={false} externalError="파일 크기 초과" />)
      expect(screen.getByText('파일 크기 초과')).toBeInTheDocument()
    })

    it('clears error display when file is removed', async () => {
      const { rerender } = render(
        <MessageInput onSend={vi.fn()} disabled={false} externalError="파일 크기 초과" />
      )
      const input = document.querySelector('input[type="file"]') as HTMLInputElement
      const file = new File(['content'], 'contract.pdf', { type: 'application/pdf' })
      await userEvent.upload(input, file)
      rerender(<MessageInput onSend={vi.fn()} disabled={false} externalError="파일 크기 초과" />)
      fireEvent.click(screen.getByRole('button', { name: /파일 제거/i }))
      expect(screen.queryByText('파일 크기 초과')).not.toBeInTheDocument()
    })
  })
})

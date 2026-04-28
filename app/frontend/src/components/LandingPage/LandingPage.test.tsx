import { render, screen } from '@testing-library/react'
import { vi } from 'vitest'
import LandingPage from './LandingPage'

describe('LandingPage', () => {
  it('renders the main title', () => {
    render(<LandingPage onSend={vi.fn()} isStreaming={false} />)
    expect(screen.getByText('AI 계약 어시스턴트')).toBeInTheDocument()
  })

  it('renders the three quick action buttons', () => {
    render(<LandingPage onSend={vi.fn()} isStreaming={false} />)
    expect(screen.getByText('과거 계약 불러오기')).toBeInTheDocument()
    expect(screen.getByText('표준계약서 찾아보기')).toBeInTheDocument()
    expect(screen.getByText('내가 가진 계약서 업로드하기')).toBeInTheDocument()
  })

  it('renders the message input textarea', () => {
    render(<LandingPage onSend={vi.fn()} isStreaming={false} />)
    expect(screen.getByRole('textbox')).toBeInTheDocument()
  })

  it('displays externalError passed from parent', () => {
    render(<LandingPage onSend={vi.fn()} isStreaming={false} externalError="파일 크기 초과" />)
    expect(screen.getByText('파일 크기 초과')).toBeInTheDocument()
  })
})

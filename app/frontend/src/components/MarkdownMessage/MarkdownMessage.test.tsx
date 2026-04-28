import { render, screen } from '@testing-library/react'
import MarkdownMessage from './MarkdownMessage'

describe('MarkdownMessage', () => {
  it('renders bold text', () => {
    render(<MarkdownMessage content="**bold**" />)
    expect(screen.getByText('bold').tagName).toBe('STRONG')
  })

  it('renders italic text', () => {
    render(<MarkdownMessage content="_italic_" />)
    expect(screen.getByText('italic').tagName).toBe('EM')
  })

  it('renders an unordered list', () => {
    render(<MarkdownMessage content={"- item1\n- item2"} />)
    expect(screen.getByText('item1')).toBeInTheDocument()
    expect(screen.getByText('item2')).toBeInTheDocument()
    expect(document.querySelector('ul')).toBeInTheDocument()
  })

  it('renders inline code', () => {
    render(<MarkdownMessage content="`console.log`" />)
    expect(screen.getByText('console.log').tagName).toBe('CODE')
  })

  it('renders a fenced code block', () => {
    render(<MarkdownMessage content={"```js\nconsole.log('hello')\n```"} />)
    expect(document.querySelector('code.language-js')).toBeInTheDocument()
  })

  it('renders plain text as-is', () => {
    render(<MarkdownMessage content="hello world" />)
    expect(screen.getByText('hello world')).toBeInTheDocument()
  })

  it('renders single newline as a line break', () => {
    const { container } = render(<MarkdownMessage content={"line one\nline two"} />)
    expect(container.querySelector('br')).toBeInTheDocument()
  })

  describe('streaming partial content', () => {
    it('renders an unclosed code block as a code block', () => {
      render(<MarkdownMessage content={"```js\nconsole.log('hello'"} />)
      expect(document.querySelector('code.language-js')).toBeInTheDocument()
    })

    it('does not modify a properly closed code block', () => {
      render(<MarkdownMessage content={"```js\nconsole.log('hello')\n```"} />)
      expect(document.querySelector('code.language-js')).toBeInTheDocument()
    })

    it('handles text after a closed code block without modification', () => {
      render(<MarkdownMessage content={"```js\nfoo()\n```\nsome text after"} />)
      expect(document.querySelector('code.language-js')).toBeInTheDocument()
      expect(screen.getByText('some text after')).toBeInTheDocument()
    })
  })
})

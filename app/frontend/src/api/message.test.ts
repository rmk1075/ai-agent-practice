import { describe, it, expect, vi, beforeEach } from 'vitest'
import { streamConversationMessage } from './message'

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

function makeDoneStream(): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder()
  return new ReadableStream({
    start(controller) {
      controller.enqueue(encoder.encode('data: [DONE]\n\n'))
      controller.close()
    },
  })
}

function makeTokenStream(token: string): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder()
  return new ReadableStream({
    start(controller) {
      controller.enqueue(encoder.encode(`data: ${JSON.stringify(token)}\n\n`))
      controller.enqueue(encoder.encode('data: [DONE]\n\n'))
      controller.close()
    },
  })
}

describe('streamConversationMessage', () => {
  beforeEach(() => mockFetch.mockReset())

  it('sends FormData (not JSON)', async () => {
    mockFetch.mockResolvedValue({ ok: true, body: makeDoneStream() })
    await streamConversationMessage(1, 'hello', undefined, undefined, vi.fn(), vi.fn(), vi.fn())
    const [, options] = mockFetch.mock.calls[0]
    expect(options.body).toBeInstanceOf(FormData)
  })

  it('sets role=user and content in FormData', async () => {
    mockFetch.mockResolvedValue({ ok: true, body: makeDoneStream() })
    await streamConversationMessage(1, 'hello', undefined, undefined, vi.fn(), vi.fn(), vi.fn())
    const [, options] = mockFetch.mock.calls[0]
    expect((options.body as FormData).get('role')).toBe('user')
    expect((options.body as FormData).get('content')).toBe('hello')
  })

  it('does not set Content-Type header', async () => {
    mockFetch.mockResolvedValue({ ok: true, body: makeDoneStream() })
    await streamConversationMessage(1, 'hello', undefined, undefined, vi.fn(), vi.fn(), vi.fn())
    const [, options] = mockFetch.mock.calls[0]
    expect(options.headers).toBeUndefined()
  })

  it('appends file to FormData when provided', async () => {
    mockFetch.mockResolvedValue({ ok: true, body: makeDoneStream() })
    const file = new File(['pdf content'], 'test.pdf', { type: 'application/pdf' })
    await streamConversationMessage(1, 'hello', file, undefined, vi.fn(), vi.fn(), vi.fn())
    const [, options] = mockFetch.mock.calls[0]
    expect((options.body as FormData).get('file')).toBe(file)
  })

  it('calls onError with server error message on 4xx', async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      json: () => Promise.resolve({ error: '파일 크기 초과' }),
    })
    const onError = vi.fn()
    await streamConversationMessage(1, 'hello', undefined, undefined, vi.fn(), vi.fn(), onError)
    expect(onError).toHaveBeenCalledWith('파일 크기 초과')
  })

  it('calls onError with default message when error body is not parseable', async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      json: () => Promise.reject(new Error('parse error')),
    })
    const onError = vi.fn()
    await streamConversationMessage(1, 'hello', undefined, undefined, vi.fn(), vi.fn(), onError)
    expect(onError).toHaveBeenCalledWith('Failed to send message.')
  })

  it('calls onDone when [DONE] is received', async () => {
    mockFetch.mockResolvedValue({ ok: true, body: makeDoneStream() })
    const onDone = vi.fn()
    await streamConversationMessage(1, 'hello', undefined, undefined, vi.fn(), onDone, vi.fn())
    expect(onDone).toHaveBeenCalled()
  })

  it('calls onToken with token data', async () => {
    mockFetch.mockResolvedValue({ ok: true, body: makeTokenStream('hello world') })
    const onToken = vi.fn()
    await streamConversationMessage(1, 'prompt', undefined, undefined, onToken, vi.fn(), vi.fn())
    expect(onToken).toHaveBeenCalledWith('hello world')
  })

  it('calls onToken with newline token correctly', async () => {
    mockFetch.mockResolvedValue({ ok: true, body: makeTokenStream('\n') })
    const onToken = vi.fn()
    await streamConversationMessage(1, 'prompt', undefined, undefined, onToken, vi.fn(), vi.fn())
    expect(onToken).toHaveBeenCalledWith('\n')
  })

  it('calls onToken with token containing newline', async () => {
    mockFetch.mockResolvedValue({ ok: true, body: makeTokenStream('line1\nline2') })
    const onToken = vi.fn()
    await streamConversationMessage(1, 'prompt', undefined, undefined, onToken, vi.fn(), vi.fn())
    expect(onToken).toHaveBeenCalledWith('line1\nline2')
  })

  it('does not append content field when content is empty string', async () => {
    mockFetch.mockResolvedValue({ ok: true, body: makeDoneStream() })
    const file = new File(['pdf'], 'test.pdf', { type: 'application/pdf' })
    await streamConversationMessage(1, '', file, undefined, vi.fn(), vi.fn(), vi.fn())
    const [, options] = mockFetch.mock.calls[0]
    expect((options.body as FormData).get('content')).toBeNull()
  })

  it('sends path in FormData when provided', async () => {
    mockFetch.mockResolvedValue({ ok: true, body: makeDoneStream() })
    const file = new File(['content'], 'test.pdf', { type: 'application/pdf' })
    await streamConversationMessage(1, 'hello', file, 'my-uuid', vi.fn(), vi.fn(), vi.fn())
    const [, options] = mockFetch.mock.calls[0]
    expect((options.body as FormData).get('path')).toBe('my-uuid')
  })

  it('does not send path in FormData when not provided', async () => {
    mockFetch.mockResolvedValue({ ok: true, body: makeDoneStream() })
    await streamConversationMessage(1, 'hello', undefined, undefined, vi.fn(), vi.fn(), vi.fn())
    const [, options] = mockFetch.mock.calls[0]
    expect((options.body as FormData).get('path')).toBeNull()
  })
})

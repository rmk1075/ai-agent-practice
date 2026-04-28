const BASE_URL = "http://localhost:8000"

export async function streamConversationMessage(
  conversationId: number,
  content: string,
  file: File | undefined,
  path: string | undefined,
  onToken: (token: string) => void,
  onDone: () => void,
  onError: (message: string) => void
) {
  const form = new FormData()
  form.append('role', 'user')
  if (content) form.append('content', content)
  if (file) form.append('file', file)
  if (path) form.append('path', path)

  const res = await fetch(`${BASE_URL}/conversations/${conversationId}/messages/`, {
    method: 'POST',
    body: form,
  })

  if (!res.ok) {
    let message = 'Failed to send message.'
    try {
      const body = await res.json()
      if (typeof body.error === 'string') message = body.error
    } catch {}
    onError(message)
    return
  }

  if (!res.body) {
    onError('No response body')
    return
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ""

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split("\n")
    buffer = lines.pop() ?? ""

    for (const line of lines) {
      // \r 만 제거 (CRLF 대응). trim()은 토큰 내 trailing space까지 제거하므로 사용 안 함
      const cleanLine = line.endsWith("\r") ? line.slice(0, -1) : line

      if (!cleanLine.startsWith("data: ")) continue

      const data = cleanLine.slice(6)
      if (data === "[DONE]") {
        onDone()
        return
      }

      if (data) onToken(data)
    }
  }
}

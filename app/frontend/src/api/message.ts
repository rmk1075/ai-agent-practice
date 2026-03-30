const BASE_URL = "http://localhost:8000"

export async function streamConversationMessage(
  conversationId: number,
  content: string,
  onToken: (token: string) => void,
  onDone: () => void
) {
  const res = await fetch(`${BASE_URL}/conversations/${conversationId}/messages/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ role: "user", content }),
  })

  if (!res.ok || !res.body) throw new Error("Failed to stream message")

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ""

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

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

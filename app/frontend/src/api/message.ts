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

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    const chunk = decoder.decode(value, { stream: true })
    for (const line of chunk.split("\n")) {
      if (!line.startsWith("data: ")) continue
      const data = line.slice(6)
      if (data === "[DONE]") {
        onDone()
        return
      }
      onToken(data)
    }
  }
}

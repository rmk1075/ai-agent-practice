export function streamChat(
  message: string,
  onToken: (token: string) => void,
  onDone: () => void
) {
  const url = `http://localhost:8000/chat/stream?message=${encodeURIComponent(message)}`

  const eventSource = new EventSource(url)

  eventSource.onmessage = (event) => {
    if (event.data === "[DONE]") {
      eventSource.close()
      onDone()
      return
    }

    onToken(event.data)
  }
}
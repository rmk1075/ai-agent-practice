import { useState } from "react"
import { streamChat } from "./api/chat"

function App() {

  const [messages, setMessages] = useState<string[]>([])
  const [input, setInput] = useState("")

  const sendMessage = () => {

    setMessages((prev) => [...prev, "User: " + input])

    let aiMessage = ""

    streamChat(input,
      (token) => {
        aiMessage += token

        setMessages((prev) => {
          const copy = [...prev]

          if (copy[copy.length - 1]?.startsWith("AI:")) {
            copy[copy.length - 1] = "AI: " + aiMessage
          } else {
            copy.push("AI: " + aiMessage)
          }

          return copy
        })
      },
      () => {}
    )

    setInput("")
  }

  return (
    <div style={{ padding: 40 }}>

      <h1>AI Chat</h1>

      <div style={{ border: "1px solid gray", padding: 20, height: 300, overflow: "auto" }}>
        {messages.map((m, i) => (
          <div key={i}>{m}</div>
        ))}
      </div>

      <input
        value={input}
        onChange={(e) => setInput(e.target.value)}
      />

      <button onClick={sendMessage}>
        Send
      </button>

    </div>
  )
}

export default App
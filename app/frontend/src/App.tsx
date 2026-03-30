import { useEffect, useState } from "react"
import { streamChat } from "./api/chat"
import { fetchConversations, createConversation } from "./api/conversations"
import type { Conversation } from "./api/conversations"

function App() {
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [messages, setMessages] = useState<string[]>([])
  const [input, setInput] = useState("")

  useEffect(() => {
    fetchConversations().then(setConversations).catch(console.error)
  }, [])

  const handleNewConversation = async () => {
    const name = `Conversation ${conversations.length + 1}`
    const created = await createConversation(name)
    setConversations((prev) => [created, ...prev])
    setSelectedId(created.id)
    setMessages([])
  }

  const handleSelectConversation = (conv: Conversation) => {
    setSelectedId(conv.id)
    setMessages([])
  }

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
    <div style={{ display: "flex", height: "100vh", fontFamily: "sans-serif" }}>

      {/* Sidebar */}
      <div style={{
        width: 240,
        borderRight: "1px solid #ddd",
        display: "flex",
        flexDirection: "column",
        background: "#f8f8f8",
      }}>
        <div style={{ padding: "16px 12px 8px" }}>
          <button
            onClick={handleNewConversation}
            style={{
              width: "100%",
              padding: "8px 0",
              background: "#1a1a1a",
              color: "#fff",
              border: "none",
              borderRadius: 6,
              cursor: "pointer",
              fontSize: 14,
            }}
          >
            + New Conversation
          </button>
        </div>

        <div style={{ flex: 1, overflowY: "auto" }}>
          {conversations.map((conv) => (
            <div
              key={conv.id}
              onClick={() => handleSelectConversation(conv)}
              style={{
                padding: "10px 14px",
                cursor: "pointer",
                background: selectedId === conv.id ? "#e0e0e0" : "transparent",
                borderRadius: 6,
                margin: "2px 8px",
                fontSize: 14,
                whiteSpace: "nowrap",
                overflow: "hidden",
                textOverflow: "ellipsis",
              }}
            >
              {conv.name}
            </div>
          ))}
        </div>
      </div>

      {/* Main chat area */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", padding: 40 }}>
        <h1 style={{ marginTop: 0 }}>AI Chat</h1>

        <div style={{ border: "1px solid gray", padding: 20, flex: 1, overflow: "auto", marginBottom: 16 }}>
          {selectedId === null ? (
            <div style={{ color: "#aaa" }}>대화를 선택하거나 새로 만들어 주세요.</div>
          ) : messages.length === 0 ? (
            <div style={{ color: "#aaa" }}>메시지를 입력해 주세요.</div>
          ) : (
            messages.map((m, i) => (
              <div key={i}>{m}</div>
            ))
          )}
        </div>

        <div style={{ display: "flex", gap: 8 }}>
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
            disabled={selectedId === null}
            style={{ flex: 1, padding: "8px 12px", fontSize: 14 }}
          />
          <button
            onClick={sendMessage}
            disabled={selectedId === null}
            style={{ padding: "8px 16px" }}
          >
            Send
          </button>
        </div>
      </div>

    </div>
  )
}

export default App

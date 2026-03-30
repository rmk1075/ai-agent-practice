import { useEffect, useState } from "react"
import { streamChat } from "./api/chat"
import { fetchConversations, createConversation, fetchConversationDetail, fetchMessages } from "./api/conversations"
import type { Conversation, ConversationDetail, Message } from "./api/conversations"

function App() {
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [selectedDetail, setSelectedDetail] = useState<ConversationDetail | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")

  useEffect(() => {
    fetchConversations().then(setConversations).catch(console.error)
  }, [])

  const handleNewConversation = async () => {
    const name = `Conversation ${conversations.length + 1}`
    const created = await createConversation(name)
    setConversations((prev) => [created, ...prev])
    setSelectedDetail({ ...created, metadata: [] })
    setMessages([])
  }

  const handleSelectConversation = async (conv: Conversation) => {
    const [detail, msgs] = await Promise.all([
      fetchConversationDetail(conv.id),
      fetchMessages(conv.id),
    ])
    setSelectedDetail(detail)
    setMessages(msgs)
  }

  const sendMessage = () => {
    const userMsg: Message = {
      id: Date.now(),
      role: "user",
      content: input,
      created_at: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, userMsg])

    let aiContent = ""

    streamChat(input,
      (token) => {
        aiContent += token

        setMessages((prev) => {
          const copy = [...prev]
          const last = copy[copy.length - 1]

          if (last?.role === "assistant") {
            copy[copy.length - 1] = { ...last, content: aiContent }
          } else {
            copy.push({
              id: Date.now() + 1,
              role: "assistant",
              content: aiContent,
              created_at: new Date().toISOString(),
            })
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
                background: selectedDetail?.id === conv.id ? "#e0e0e0" : "transparent",
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
          {selectedDetail === null ? (
            <div style={{ color: "#aaa" }}>대화를 선택하거나 새로 만들어 주세요.</div>
          ) : messages.length === 0 ? (
            <div style={{ color: "#aaa" }}>메시지를 입력해 주세요.</div>
          ) : (
            messages.map((m) => (
              <div key={m.id} style={{ marginBottom: 8 }}>
                <strong>{m.role === "user" ? "User" : "AI"}:</strong> {m.content}
              </div>
            ))
          )}
        </div>

        <div style={{ display: "flex", gap: 8 }}>
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
            disabled={selectedDetail === null}
            style={{ flex: 1, padding: "8px 12px", fontSize: 14 }}
          />
          <button
            onClick={sendMessage}
            disabled={selectedDetail === null}
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

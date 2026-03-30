import { useEffect, useRef, useState, type MouseEvent } from "react"
import { streamConversationMessage } from "./api/message"
import { fetchConversations, createConversation, fetchConversationDetail, fetchMessages, deleteConversation } from "./api/conversations"
import type { Conversation, ConversationDetail, Message } from "./api/conversations"

function App() {
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [selectedDetail, setSelectedDetail] = useState<ConversationDetail | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const activeConvIdRef = useRef<number | null>(null)

  useEffect(() => {
    fetchConversations().then(setConversations).catch(console.error)
  }, [])

  const handleNewConversation = async () => {
    const name = `Conversation ${conversations.length + 1}`
    const created = await createConversation(name)
    setConversations((prev) => [created, ...prev])
    activeConvIdRef.current = created.id
    setSelectedDetail({ ...created, metadata: [] })
    setMessages([])
  }

  const handleDeleteConversation = async (e: MouseEvent, convId: number) => {
    e.stopPropagation()
    await deleteConversation(convId)
    setConversations((prev) => prev.filter((c: Conversation) => c.id !== convId))
    if (activeConvIdRef.current === convId) {
      activeConvIdRef.current = null
      setSelectedDetail(null)
      setMessages([])
    }
  }

  const handleSelectConversation = async (conv: Conversation) => {
    activeConvIdRef.current = conv.id
    const [detail, msgs] = await Promise.all([
      fetchConversationDetail(conv.id),
      fetchMessages(conv.id),
    ])
    setSelectedDetail(detail)
    setMessages(msgs)
  }

  const sendMessage = async () => {
    if (!selectedDetail) return
    const content = input
    const conversationId = selectedDetail.id
    setInput("")

    // 낙관적으로 유저 메시지 표시 (백엔드가 실제 저장)
    if (activeConvIdRef.current === conversationId) {
      setMessages((prev: Message[]) => [...prev, {
        id: Date.now(),
        role: "user",
        content,
        created_at: new Date().toISOString(),
      }])
    }

    let aiContent = ""

    await streamConversationMessage(conversationId, content,
      (token) => {
        aiContent += token  // 항상 누적

        if (activeConvIdRef.current !== conversationId) return

        setMessages((prev: Message[]) => {
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
      () => {}  // 백엔드가 AI 메시지 저장 처리
    )
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
                display: "flex",
                alignItems: "center",
                padding: "10px 14px",
                cursor: "pointer",
                background: selectedDetail?.id === conv.id ? "#e0e0e0" : "transparent",
                borderRadius: 6,
                margin: "2px 8px",
                fontSize: 14,
              }}
            >
              <span style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                {conv.name}
              </span>
              <button
                onClick={(e) => handleDeleteConversation(e, conv.id)}
                style={{
                  flexShrink: 0,
                  marginLeft: 6,
                  background: "none",
                  border: "none",
                  cursor: "pointer",
                  color: "#999",
                  fontSize: 16,
                  lineHeight: 1,
                  padding: "0 2px",
                }}
              >
                ×
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Main conversation area */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", padding: 40 }}>
        <h1 style={{ marginTop: 0 }}>AI Conversation</h1>

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

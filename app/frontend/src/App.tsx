import { useEffect, useRef, useState, type MouseEvent } from 'react'
import { streamConversationMessage } from './api/message'
import {
  fetchConversations,
  createConversation,
  fetchConversationDetail,
  fetchMessages,
  deleteConversation,
} from './api/conversations'
import type { Conversation, ConversationDetail, Message } from './api/conversations'
import { saveFile, deleteFile } from './lib/fileStorage'
import Header from './components/Header/Header'
import Sidebar from './components/Sidebar/Sidebar'
import LandingPage from './components/LandingPage/LandingPage'
import ChatView from './components/ChatView/ChatView'
import './App.css'

function App() {
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [selectedDetail, setSelectedDetail] = useState<ConversationDetail | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [externalError, setExternalError] = useState<string | undefined>(undefined)
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
    setSidebarOpen(false)
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
    setSidebarOpen(false)
  }

  const handleSend = async (content: string, file?: File) => {
    setExternalError(undefined)
    let convId = selectedDetail?.id
    if (!convId) {
      const name = `Conversation ${conversations.length + 1}`
      const created = await createConversation(name)
      setConversations((prev) => [created, ...prev])
      activeConvIdRef.current = created.id
      setSelectedDetail({ ...created, metadata: [] })
      setMessages([])
      convId = created.id
    }

    const conversationId = convId
    const path = file ? crypto.randomUUID() : undefined
    if (file && path) await saveFile(path, file)

    setIsStreaming(true)

    if (activeConvIdRef.current === conversationId) {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now(),
          role: 'user',
          content,
          file: file && path ? { id: 0, filename: file.name, path } : null,
          created_at: new Date().toISOString(),
        },
      ])
    }

    let aiContent = ''
    await streamConversationMessage(
      conversationId,
      content,
      file,
      path,
      (token) => {
        aiContent += token
        if (activeConvIdRef.current !== conversationId) return
        setMessages((prev) => {
          const copy = [...prev]
          const last = copy[copy.length - 1]
          if (last?.role === 'assistant') {
            copy[copy.length - 1] = { ...last, content: aiContent }
          } else {
            copy.push({
              id: Date.now() + 1,
              role: 'assistant',
              content: aiContent,
              file: null,
              created_at: new Date().toISOString(),
            })
          }
          return copy
        })
      },
      () => {},
      async (message) => {
        if (path) await deleteFile(path)
        setExternalError(message)
      }
    )
    setIsStreaming(false)
  }

  return (
    <>
      <Header onToggleSidebar={() => setSidebarOpen((o) => !o)} />
      <Sidebar
        isOpen={sidebarOpen}
        conversations={conversations}
        selectedId={selectedDetail?.id ?? null}
        onSelect={handleSelectConversation}
        onDelete={handleDeleteConversation}
        onNewConversation={handleNewConversation}
        onClose={() => setSidebarOpen(false)}
      />
      {messages.length === 0 ? (
        <LandingPage onSend={handleSend} isStreaming={isStreaming} externalError={externalError} />
      ) : (
        <ChatView messages={messages} onSend={handleSend} isStreaming={isStreaming} externalError={externalError} />
      )}
    </>
  )
}

export default App

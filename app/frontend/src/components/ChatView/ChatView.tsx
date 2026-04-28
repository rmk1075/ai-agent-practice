import { useEffect, useRef } from 'react'
import type { Message } from '../../api/conversations'
import MessageInput from '../MessageInput/MessageInput'
import styles from './ChatView.module.css'

interface ChatViewProps {
  messages: Message[]
  onSend: (content: string, file?: File) => void
  isStreaming: boolean
  externalError?: string
}

export default function ChatView({ messages, onSend, isStreaming, externalError }: ChatViewProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (bottomRef.current && typeof bottomRef.current.scrollIntoView === 'function') {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages])

  return (
    <div className={styles.container}>
      <div className={styles.messages}>
        {messages.map((m) => (
          <div
            key={m.id}
            className={`${styles.bubble} ${m.role === 'user' ? styles.userBubble : styles.aiBubble}`}
          >
            {m.content}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
      <div className={styles.inputArea}>
        <MessageInput onSend={onSend} disabled={isStreaming} externalError={externalError} />
      </div>
    </div>
  )
}

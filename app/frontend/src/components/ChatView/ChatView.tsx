import { useEffect, useRef } from 'react'
import type { Message, MessageFile } from '../../api/conversations'
import { getFile } from '../../lib/fileStorage'
import MessageInput from '../MessageInput/MessageInput'
import styles from './ChatView.module.css'
import MarkdownMessage from '../MarkdownMessage/MarkdownMessage'

interface ChatViewProps {
  messages: Message[]
  onSend: (content: string, file?: File) => void
  isStreaming: boolean
  externalError?: string
}

function FileCard({ fileInfo }: { fileInfo: MessageFile }) {
  const handleClick = async () => {
    const file = await getFile(fileInfo.path)
    if (!file) return
    const url = URL.createObjectURL(file)
    const a = document.createElement('a')
    a.href = url
    a.download = fileInfo.filename
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className={styles.fileCard} onClick={handleClick} role="button" tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && handleClick()}>
      <span className={styles.fileIcon}>📎</span>
      <span className={styles.fileName}>{fileInfo.filename}</span>
    </div>
  )
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
            {m.file && <FileCard fileInfo={m.file} />}
            <MarkdownMessage content={m.content} />
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

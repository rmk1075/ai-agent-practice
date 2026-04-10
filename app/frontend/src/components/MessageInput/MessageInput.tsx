import { useState, useRef } from 'react'
import styles from './MessageInput.module.css'

interface MessageInputProps {
  onSend: (content: string) => void
  disabled: boolean
}

export default function MessageInput({ onSend, disabled }: MessageInputProps) {
  const [value, setValue] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const handleSend = () => {
    const trimmed = value.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setValue('')
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setValue(e.target.value)
    const el = e.target
    el.style.height = 'auto'
    el.style.height = `${el.scrollHeight}px`
  }

  return (
    <div className={styles.container}>
      <div className={styles.icons}>
        <span className={styles.icon}>📎</span>
        <span className={styles.icon}>📄</span>
      </div>
      <textarea
        ref={textareaRef}
        className={styles.textarea}
        value={value}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        placeholder="계약 상황을 편하게 말씀해 주세요. AI가 내용을 분석해 가장 적합한 표준계약서를 추천해 드립니다."
        rows={1}
        disabled={disabled}
      />
      <button
        className={styles.sendButton}
        onClick={handleSend}
        disabled={disabled}
        aria-label="send"
      >
        ↑
      </button>
    </div>
  )
}

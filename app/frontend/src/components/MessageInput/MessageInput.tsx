import { useState, useRef, useEffect } from 'react'
import styles from './MessageInput.module.css'

interface MessageInputProps {
  onSend: (content: string, file?: File) => void
  disabled: boolean
  externalError?: string
}

export default function MessageInput({ onSend, disabled, externalError }: MessageInputProps) {
  const [value, setValue] = useState('')
  const [file, setFile] = useState<File | undefined>(undefined)
  const [error, setError] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    setError(externalError ?? '')
  }, [externalError])

  const handleSend = () => {
    const trimmed = value.trim()
    if (!trimmed && !file) return
    if (disabled) return
    onSend(trimmed, file)
    setValue('')
    setFile(undefined)
    setError('')
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

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0]
    if (selected) {
      setFile(selected)
      setError('')
    }
  }

  const handleRemoveFile = () => {
    setFile(undefined)
    setError('')
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  return (
    <div className={styles.container}>
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.docx"
        style={{ display: 'none' }}
        onChange={handleFileChange}
      />
      <div className={styles.inputArea}>
        {(file || error) && (
          <div className={styles.badgeRow}>
            {file && (
              <span className={styles.badge}>
                📄 {file.name}
                <button
                  className={styles.badgeRemove}
                  onClick={handleRemoveFile}
                  aria-label="파일 제거"
                  type="button"
                >
                  ✕
                </button>
              </span>
            )}
            {error && <span className={styles.errorText}>{error}</span>}
          </div>
        )}
        <div className={styles.inputRow}>
          <span
            className={styles.icon}
            onClick={() => fileInputRef.current?.click()}
            role="button"
            aria-label="파일 첨부"
            tabIndex={0}
            onKeyDown={(e) => e.key === 'Enter' && fileInputRef.current?.click()}
          >
            📎
          </span>
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
      </div>
    </div>
  )
}

import MessageInput from '../MessageInput/MessageInput'
import styles from './LandingPage.module.css'

interface LandingPageProps {
  onSend: (content: string) => void
  isStreaming: boolean
}

const QUICK_ACTIONS = [
  '과거 계약 불러오기',
  '표준계약서 찾아보기',
  '내가 가진 계약서 업로드하기',
]

export default function LandingPage({ onSend, isStreaming }: LandingPageProps) {
  return (
    <div className={styles.container}>
      <div className={styles.hero}>
        <span className={styles.dot} />
        <h1 className={styles.title}>AI 계약 어시스턴트</h1>
      </div>
      <div className={styles.inputWrapper}>
        <MessageInput onSend={onSend} disabled={isStreaming} />
      </div>
      <div className={styles.actions}>
        {QUICK_ACTIONS.map((label) => (
          <button key={label} className={styles.actionButton}>
            {label}
          </button>
        ))}
      </div>
    </div>
  )
}

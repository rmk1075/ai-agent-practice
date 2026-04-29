import { Link } from 'react-router-dom'
import styles from './Header.module.css'

interface HeaderProps {
  onToggleSidebar: () => void
}

export default function Header({ onToggleSidebar }: HeaderProps) {
  return (
    <header className={styles.header}>
      <button
        className={styles.hamburger}
        onClick={onToggleSidebar}
        aria-label="menu"
      >
        ☰
      </button>
      <Link to="/" className={styles.title}>
        <span className={styles.dot} />
        AI 계약 어시스턴트
      </Link>
    </header>
  )
}

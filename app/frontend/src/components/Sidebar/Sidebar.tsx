import type { MouseEvent } from 'react'
import type { Conversation } from '../../api/conversations'
import styles from './Sidebar.module.css'

interface SidebarProps {
  isOpen: boolean
  conversations: Conversation[]
  selectedId: number | null
  onSelect: (conv: Conversation) => void
  onDelete: (e: MouseEvent, convId: number) => void
  onNewConversation: () => void
  onClose: () => void
}

export default function Sidebar({
  isOpen,
  conversations,
  selectedId,
  onSelect,
  onDelete,
  onNewConversation,
  onClose,
}: SidebarProps) {
  if (!isOpen) return null

  return (
    <div
      className={styles.overlay}
      data-testid="sidebar-overlay"
      onClick={onClose}
    >
      <div className={styles.panel} onClick={(e) => e.stopPropagation()}>
        <button className={styles.newButton} onClick={onNewConversation}>
          + New Conversation
        </button>
        <div className={styles.list}>
          {conversations.map((conv) => (
            <div
              key={conv.id}
              className={`${styles.item} ${selectedId === conv.id ? styles.itemActive : ''}`}
              onClick={() => onSelect(conv)}
            >
              <span className={styles.itemName}>{conv.name}</span>
              <button
                className={styles.deleteButton}
                onClick={(e) => onDelete(e, conv.id)}
                aria-label={`delete ${conv.name}`}
              >
                ×
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

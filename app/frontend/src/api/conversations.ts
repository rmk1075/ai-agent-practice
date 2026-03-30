const BASE_URL = "http://localhost:8000"

export interface Conversation {
  id: number
  name: string
  created_at: string
  updated_at: string
}

export interface ConversationMetadata {
  key: string
  value: string
}

export interface ConversationDetail extends Conversation {
  metadata: ConversationMetadata[]
}

export interface Message {
  id: number
  role: "user" | "assistant" | "system"
  content: string
  created_at: string
}

export async function fetchConversations(): Promise<Conversation[]> {
  const res = await fetch(`${BASE_URL}/conversations/`)
  if (!res.ok) throw new Error("Failed to fetch conversations")
  return res.json()
}

export async function fetchConversationDetail(id: number): Promise<ConversationDetail> {
  const res = await fetch(`${BASE_URL}/conversations/${id}/`)
  if (!res.ok) throw new Error("Failed to fetch conversation detail")
  return res.json()
}

export async function fetchMessages(conversationId: number): Promise<Message[]> {
  const res = await fetch(`${BASE_URL}/conversations/${conversationId}/messages/`)
  if (!res.ok) throw new Error("Failed to fetch messages")
  return res.json()
}

export async function createConversation(name: string): Promise<Conversation> {
  const res = await fetch(`${BASE_URL}/conversations/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  })
  if (!res.ok) throw new Error("Failed to create conversation")
  return res.json()
}

export async function createMessage(
  conversationId: number,
  role: Message["role"],
  content: string
): Promise<Message> {
  const res = await fetch(`${BASE_URL}/conversations/${conversationId}/messages/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ role, content }),
  })
  if (!res.ok) throw new Error("Failed to create message")
  return res.json()
}

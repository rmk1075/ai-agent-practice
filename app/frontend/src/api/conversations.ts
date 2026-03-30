const BASE_URL = "http://localhost:8000"

export interface Conversation {
  id: number
  name: string
  created_at: string
  updated_at: string
}

export async function fetchConversations(): Promise<Conversation[]> {
  const res = await fetch(`${BASE_URL}/conversations/`)
  if (!res.ok) throw new Error("Failed to fetch conversations")
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

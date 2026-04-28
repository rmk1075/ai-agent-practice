import { openDB } from 'idb'

const DB_NAME = 'ai-agent-files'
const STORE_NAME = 'attachments'
const DB_VERSION = 1

async function getDB() {
  return openDB(DB_NAME, DB_VERSION, {
    upgrade(db) {
      db.createObjectStore(STORE_NAME)
    },
  })
}

export async function saveFile(path: string, file: File): Promise<void> {
  const db = await getDB()
  await db.put(STORE_NAME, file, path)
}

export async function getFile(path: string): Promise<File | undefined> {
  const db = await getDB()
  return db.get(STORE_NAME, path)
}

export async function deleteFile(path: string): Promise<void> {
  const db = await getDB()
  await db.delete(STORE_NAME, path)
}

import { describe, it, expect, vi, beforeEach } from 'vitest'

const store = new Map<string, unknown>()

vi.mock('idb', () => ({
  openDB: vi.fn().mockResolvedValue({
    put: vi.fn().mockImplementation((_storeName: string, value: unknown, key: string) => {
      store.set(key, value)
      return Promise.resolve()
    }),
    get: vi.fn().mockImplementation((_storeName: string, key: string) => {
      return Promise.resolve(store.get(key))
    }),
    delete: vi.fn().mockImplementation((_storeName: string, key: string) => {
      store.delete(key)
      return Promise.resolve()
    }),
  }),
}))

import { saveFile, getFile, deleteFile } from './fileStorage'

describe('fileStorage', () => {
  beforeEach(() => {
    store.clear()
  })

  it('saves and retrieves a file by path', async () => {
    const file = new File(['hello pdf'], 'test.pdf', { type: 'application/pdf' })
    await saveFile('uuid-1', file)
    const result = await getFile('uuid-1')
    expect(result).toBe(file)
  })

  it('returns undefined for unknown path', async () => {
    const result = await getFile('nonexistent')
    expect(result).toBeUndefined()
  })

  it('deletes a file by path', async () => {
    const file = new File(['content'], 'doc.docx', { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' })
    await saveFile('uuid-2', file)
    await deleteFile('uuid-2')
    const result = await getFile('uuid-2')
    expect(result).toBeUndefined()
  })
})

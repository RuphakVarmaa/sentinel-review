import axios from 'axios'
import type { ReviewResult, Finding } from './types'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://sentinel-review-api.railway.app'

export const api = axios.create({ baseURL: API_URL })

export async function submitReview(diff: string, context?: string, prUrl?: string): Promise<ReviewResult> {
  const { data } = await api.post('/v1/review', { diff, context, pr_url: prUrl, source: 'web' })
  return data
}

export async function getSharedReview(shareId: string): Promise<ReviewResult | null> {
  try {
    const { data } = await api.get(`/shares/${shareId}`)
    return data
  } catch {
    return null
  }
}

export async function submitFeedback(findingId: string, feedback: 'helpful' | 'unhelpful'): Promise<void> {
  await api.post(`/v1/findings/${findingId}/feedback`, { feedback })
}

export function streamReview(
  diff: string,
  context: string | undefined,
  onStatus: (msg: string) => void,
  onFinding: (finding: Finding) => void,
  onSummary: (summary: Record<string, unknown>) => void,
  onDone: () => void,
  onError: (err: Error) => void
): AbortController {
  const controller = new AbortController()

  const run = async () => {
    try {
      const response = await fetch(`${API_URL}/v1/review/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ diff, context, source: 'web' }),
        signal: controller.signal,
      })

      if (!response.ok) throw new Error(`API error: ${response.status}`)

      const reader = response.body?.getReader()
      if (!reader) throw new Error('No response body')

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })

        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        let eventType = ''
        let dataLine = ''

        for (const line of lines) {
          if (line.startsWith('event: ')) eventType = line.slice(7).trim()
          else if (line.startsWith('data: ')) {
            dataLine = line.slice(6).trim()
            if (eventType && dataLine) {
              try {
                const parsed = JSON.parse(dataLine)
                if (eventType === 'status') onStatus(parsed.message || '')
                else if (eventType === 'finding') onFinding(parsed as Finding)
                else if (eventType === 'summary') onSummary(parsed)
                else if (eventType === 'done') onDone()
              } catch { /* ignore parse errors */ }
              eventType = ''
              dataLine = ''
            }
          }
        }
      }
    } catch (err) {
      if ((err as Error).name !== 'AbortError') onError(err as Error)
    }
  }

  run()
  return controller
}

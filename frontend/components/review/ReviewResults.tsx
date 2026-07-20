'use client'
import { Finding, ReviewSummary } from '@/lib/types'
import { SummaryCard } from './SummaryCard'
import { FindingCard } from './FindingCard'
import { severityOrder } from '@/lib/utils'

interface Props {
  findings: Finding[]
  summary: ReviewSummary | null
  shareId?: string
  isStreaming?: boolean
  statusMessage?: string
}

export function ReviewResults({ findings, summary, shareId, isStreaming, statusMessage }: Props) {
  const sorted = [...findings].sort((a, b) => severityOrder(a.severity) - severityOrder(b.severity))

  if (!summary && findings.length === 0) {
    if (isStreaming) {
      return (
        <div className="flex flex-col items-center justify-center h-64 gap-3 text-gray-400">
          <div className="h-8 w-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-sm animate-pulse-slow">{statusMessage || 'Analyzing...'}</p>
        </div>
      )
    }
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-3 text-gray-400">
        <div className="text-6xl">🔍</div>
        <p className="text-sm">Run a review to see results here</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {summary && <SummaryCard summary={summary} shareId={shareId} />}
      {isStreaming && statusMessage && (
        <div className="flex items-center gap-2 text-sm text-blue-600">
          <div className="h-3 w-3 border border-blue-500 border-t-transparent rounded-full animate-spin" />
          {statusMessage}
        </div>
      )}
      {sorted.length > 0 && (
        <div className="space-y-3">
          <h3 className="font-medium text-gray-700 text-sm">{sorted.length} findings</h3>
          {sorted.map((f, i) => <FindingCard key={f.id || i} finding={f} index={i} />)}
        </div>
      )}
    </div>
  )
}

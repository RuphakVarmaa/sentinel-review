import { SeverityBadge } from './SeverityBadge'
import { formatDuration } from '@/lib/utils'
import type { ReviewSummary } from '@/lib/types'

interface Props {
  summary: ReviewSummary
  shareId?: string
}

export function SummaryCard({ summary, shareId }: Props) {
  const counts = summary.finding_counts
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-5 shadow-sm">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <span className="text-sm font-medium text-gray-500">Overall</span>
          <SeverityBadge severity={summary.overall_severity} size="lg" />
        </div>
        <div className="flex items-center gap-2 text-xs text-gray-400">
          <span className="bg-gray-100 px-2 py-1 rounded">{formatDuration(summary.latency_ms)}</span>
          <span className="bg-gray-100 px-2 py-1 rounded">{summary.model_used}</span>
          <span className="bg-gray-100 px-2 py-1 rounded">{summary.line_count} lines</span>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap gap-3">
        {counts.critical > 0 && <span className="text-red-600 font-semibold text-sm">{counts.critical} critical</span>}
        {counts.high > 0 && <span className="text-orange-600 font-semibold text-sm">{counts.high} high</span>}
        {counts.medium > 0 && <span className="text-yellow-600 font-semibold text-sm">{counts.medium} medium</span>}
        {counts.low > 0 && <span className="text-blue-600 font-semibold text-sm">{counts.low} low</span>}
        {counts.info > 0 && <span className="text-gray-500 font-semibold text-sm">{counts.info} info</span>}
        {summary.total_findings === 0 && <span className="text-green-600 font-semibold text-sm">No issues found</span>}
      </div>

      {shareId && (
        <div className="mt-3 pt-3 border-t border-gray-100 flex items-center gap-2">
          <span className="text-xs text-gray-400">Share:</span>
          <code className="text-xs bg-gray-100 px-2 py-1 rounded select-all">
            {typeof window !== 'undefined' ? `${window.location.origin}/review/${shareId}` : `/review/${shareId}`}
          </code>
        </div>
      )}
    </div>
  )
}

'use client'
import { useState } from 'react'
import { motion } from 'framer-motion'
import { ChevronDown, ThumbsUp, ThumbsDown } from 'lucide-react'
import { SeverityBadge } from './SeverityBadge'
import { cn, CATEGORY_CONFIG } from '@/lib/utils'
import type { Finding } from '@/lib/types'

interface Props {
  finding: Finding
  index: number
}

export function FindingCard({ finding, index }: Props) {
  const [showFix, setShowFix] = useState(false)
  const [showWhy, setShowWhy] = useState(false)
  const [feedback, setFeedback] = useState<'helpful' | 'unhelpful' | null>(null)
  const catConfig = CATEGORY_CONFIG[finding.category] || { label: finding.category, icon: '📋' }

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.05 }}
      className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm"
    >
      <div className="flex items-start gap-3">
        <SeverityBadge severity={finding.severity} size="sm" />
        <span className="text-sm text-gray-500 flex items-center gap-1">
          <span>{catConfig.icon}</span>
          <span>{catConfig.label}</span>
        </span>
        {finding.file_path && (
          <span className="text-xs font-mono text-gray-400 ml-auto truncate max-w-[200px]">
            {finding.file_path}{finding.line_start ? `:${finding.line_start}` : ''}
          </span>
        )}
      </div>

      <h3 className="mt-2 font-semibold text-gray-900">{finding.title}</h3>
      <p className="mt-1 text-sm text-gray-600 leading-relaxed">{finding.explanation}</p>

      {finding.cwe_id && (
        <span className="mt-2 inline-block text-xs text-blue-600 bg-blue-50 px-2 py-0.5 rounded">
          {finding.cwe_id}
        </span>
      )}

      <div className="mt-3 space-y-2">
        {finding.suggested_fix && (
          <button
            onClick={() => setShowFix(!showFix)}
            className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800 font-medium"
          >
            <ChevronDown className={cn('h-4 w-4 transition-transform', showFix && 'rotate-180')} />
            Suggested Fix
          </button>
        )}
        {showFix && finding.suggested_fix && (
          <pre className="bg-gray-900 text-green-400 text-xs p-3 rounded-lg overflow-x-auto whitespace-pre-wrap">
            {finding.suggested_fix}
          </pre>
        )}

        {finding.why_it_matters && (
          <button
            onClick={() => setShowWhy(!showWhy)}
            className="flex items-center gap-1 text-sm text-purple-600 hover:text-purple-800 font-medium"
          >
            <ChevronDown className={cn('h-4 w-4 transition-transform', showWhy && 'rotate-180')} />
            Why This Matters
          </button>
        )}
        {showWhy && finding.why_it_matters && (
          <p className="text-sm text-gray-600 bg-purple-50 border border-purple-100 p-3 rounded-lg">
            {finding.why_it_matters}
          </p>
        )}
      </div>

      <div className="mt-3 flex items-center gap-2 pt-2 border-t border-gray-100">
        <span className="text-xs text-gray-400">Helpful?</span>
        <button
          onClick={() => setFeedback('helpful')}
          className={cn('p-1 rounded hover:bg-green-50', feedback === 'helpful' && 'text-green-600 bg-green-50')}
        >
          <ThumbsUp className="h-3.5 w-3.5" />
        </button>
        <button
          onClick={() => setFeedback('unhelpful')}
          className={cn('p-1 rounded hover:bg-red-50', feedback === 'unhelpful' && 'text-red-600 bg-red-50')}
        >
          <ThumbsDown className="h-3.5 w-3.5" />
        </button>
      </div>
    </motion.div>
  )
}

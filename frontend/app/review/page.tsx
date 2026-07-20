'use client'
import { useState, useCallback } from 'react'
import { Copy, Share2, Upload, Github, FileText, Play, Loader2 } from 'lucide-react'
import Link from 'next/link'
import dynamic from 'next/dynamic'
import { streamReview } from '@/lib/api'
import { ReviewResults } from '@/components/review/ReviewResults'
import { SAMPLE_DIFF } from '@/lib/sample-diff'
import type { Finding, ReviewSummary } from '@/lib/types'

const DiffEditor = dynamic(() => import('@/components/review/DiffEditor').then(m => ({ default: m.DiffEditor })), {
  ssr: false,
  loading: () => <div className="h-[400px] bg-gray-900 rounded-lg animate-pulse" />
})

type InputTab = 'paste' | 'github' | 'upload'

export default function ReviewPage() {
  const [activeTab, setActiveTab] = useState<InputTab>('paste')
  const [diff, setDiff] = useState('')
  const [context, setContext] = useState('')
  const [prUrl, setPrUrl] = useState('')
  const [isRunning, setIsRunning] = useState(false)
  const [findings, setFindings] = useState<Finding[]>([])
  const [summary, setSummary] = useState<ReviewSummary | null>(null)
  const [statusMessage, setStatusMessage] = useState('')
  const [shareId, setShareId] = useState<string | undefined>()
  const [error, setError] = useState('')

  const canRun = (diff.trim().length > 0 || prUrl.trim().length > 0) && !isRunning

  const handleRun = useCallback(() => {
    if (!canRun) return
    setIsRunning(true)
    setFindings([])
    setSummary(null)
    setError('')
    setShareId(undefined)
    setStatusMessage('Initializing...')

    streamReview(
      diff,
      context || undefined,
      (msg) => setStatusMessage(msg),
      (finding) => setFindings(prev => [...prev, finding]),
      (s) => {
        setSummary({
          overall_severity: s.overall_severity as string,
          finding_counts: s.finding_counts as ReviewSummary['finding_counts'],
          model_used: s.model_used as string,
          latency_ms: s.latency_ms as number,
          line_count: s.line_count as number,
          total_findings: s.total_findings as number,
        })
        if (s.share_id) setShareId(s.share_id as string)
      },
      () => { setIsRunning(false); setStatusMessage('') },
      (err) => { setError(err.message); setIsRunning(false) }
    )
  }, [diff, context, canRun])

  const handleCopyMarkdown = () => {
    if (!summary || findings.length === 0) return
    const md = [
      `# Sentinel Review: ${summary.overall_severity}`,
      '',
      `**${summary.total_findings} findings** · ${summary.model_used} · ${summary.latency_ms}ms`,
      '',
      ...findings.map(f =>
        `## ${f.severity.toUpperCase()}: ${f.title}\n**Category:** ${f.category}\n${f.file_path ? `**File:** \`${f.file_path}\`${f.line_start ? ` L${f.line_start}` : ''}\n` : ''}${f.explanation}\n${f.cwe_id ? `**CWE:** ${f.cwe_id}\n` : ''}`
      )
    ].join('\n')
    navigator.clipboard.writeText(md)
  }

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = (ev) => setDiff(ev.target?.result as string || '')
    reader.readAsText(file)
    setActiveTab('paste')
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top nav */}
      <nav className="bg-white border-b border-gray-200 px-6 py-3 flex items-center gap-4">
        <Link href="/" className="flex items-center gap-2">
          <span className="text-xl">🛡️</span>
          <span className="font-bold text-gray-900 text-sm">Sentinel Review</span>
        </Link>
        <span className="text-gray-300">/</span>
        <span className="text-sm text-gray-500">Code Review</span>
      </nav>

      <div className="max-w-[1400px] mx-auto px-6 py-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* LEFT — Input */}
        <div className="space-y-4">
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
            {/* Tabs */}
            <div className="flex border-b border-gray-200">
              {(['paste', 'github', 'upload'] as InputTab[]).map(tab => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`flex-1 py-3 text-sm font-medium flex items-center justify-center gap-1.5 transition-colors ${
                    activeTab === tab
                      ? 'border-b-2 border-gray-900 text-gray-900'
                      : 'text-gray-400 hover:text-gray-600'
                  }`}
                >
                  {tab === 'paste' && <><FileText className="h-3.5 w-3.5" /> Paste Diff</>}
                  {tab === 'github' && <><Github className="h-3.5 w-3.5" /> GitHub PR URL</>}
                  {tab === 'upload' && <><Upload className="h-3.5 w-3.5" /> Upload File</>}
                </button>
              ))}
            </div>

            <div className="p-4">
              {activeTab === 'paste' && (
                <>
                  <div className="flex items-center justify-between mb-2">
                    <div className="text-xs text-gray-400">
                      {diff.split('\n').length} lines · {diff.length} chars
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => setDiff(SAMPLE_DIFF)}
                        className="text-xs text-blue-600 hover:text-blue-800"
                      >
                        Load example
                      </button>
                      <button
                        onClick={() => setDiff('')}
                        className="text-xs text-gray-400 hover:text-gray-600"
                      >
                        Clear
                      </button>
                    </div>
                  </div>
                  <DiffEditor value={diff} onChange={setDiff} />
                </>
              )}

              {activeTab === 'github' && (
                <div className="space-y-3">
                  <input
                    type="url"
                    placeholder="https://github.com/owner/repo/pull/123"
                    value={prUrl}
                    onChange={e => setPrUrl(e.target.value)}
                    className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-gray-900"
                  />
                  <p className="text-xs text-gray-400">Only public repositories are supported without authentication.</p>
                </div>
              )}

              {activeTab === 'upload' && (
                <div className="border-2 border-dashed border-gray-200 rounded-lg p-8 text-center">
                  <Upload className="h-8 w-8 text-gray-300 mx-auto mb-3" />
                  <p className="text-sm text-gray-500 mb-3">Drop a .diff or .patch file</p>
                  <label className="cursor-pointer bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm px-4 py-2 rounded-lg">
                    Browse file
                    <input type="file" accept=".diff,.patch" onChange={handleFileUpload} className="hidden" />
                  </label>
                </div>
              )}
            </div>
          </div>

          {/* Context input */}
          <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
            <label className="text-sm font-medium text-gray-700 block mb-2">
              Context <span className="text-gray-400 font-normal">(optional)</span>
            </label>
            <input
              type="text"
              placeholder="What does this PR do? e.g. 'Add OAuth2 login with GitHub'"
              value={context}
              onChange={e => setContext(e.target.value)}
              maxLength={500}
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-900"
            />
          </div>

          {/* Run button */}
          <button
            onClick={handleRun}
            disabled={!canRun}
            className="w-full py-4 bg-gray-900 text-white rounded-xl font-semibold text-base hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition-all"
          >
            {isRunning ? (
              <><Loader2 className="h-5 w-5 animate-spin" /> Analyzing... (~8 seconds)</>
            ) : (
              <><Play className="h-5 w-5" /> Run Review</>
            )}
          </button>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3 rounded-lg">
              {error}
            </div>
          )}
        </div>

        {/* RIGHT — Results */}
        <div className="space-y-4">
          {summary && (
            <div className="flex items-center gap-2 justify-end">
              <button onClick={handleCopyMarkdown} className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-gray-900 border border-gray-200 px-3 py-1.5 rounded-lg bg-white">
                <Copy className="h-3.5 w-3.5" /> Copy as Markdown
              </button>
              {shareId && (
                <button
                  onClick={() => navigator.clipboard.writeText(`${window.location.origin}/review/${shareId}`)}
                  className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-gray-900 border border-gray-200 px-3 py-1.5 rounded-lg bg-white"
                >
                  <Share2 className="h-3.5 w-3.5" /> Copy Share Link
                </button>
              )}
            </div>
          )}
          <ReviewResults
            findings={findings}
            summary={summary}
            shareId={shareId}
            isStreaming={isRunning}
            statusMessage={statusMessage}
          />
        </div>
      </div>
    </div>
  )
}

export type Severity = 'critical' | 'high' | 'medium' | 'low' | 'info'
export type Category = 'security' | 'logic' | 'performance' | 'style' | 'maintainability' | 'accessibility'

export interface Finding {
  id: string
  category: Category
  severity: Severity
  file_path?: string
  line_start?: number
  line_end?: number
  title: string
  explanation: string
  suggested_fix?: string
  why_it_matters?: string
  cwe_id?: string
  user_feedback?: 'helpful' | 'unhelpful'
}

export interface FindingCounts {
  critical: number
  high: number
  medium: number
  low: number
  info: number
}

export interface ReviewSummary {
  overall_severity: string
  finding_counts: FindingCounts
  model_used: string
  latency_ms: number
  line_count: number
  total_findings: number
}

export interface ReviewResult {
  review_id: string
  share_id?: string
  overall_severity: Severity | 'PASS'
  finding_counts: FindingCounts
  model_used: string
  latency_ms: number
  findings: Finding[]
}

export interface SSEEvent {
  type: 'status' | 'finding' | 'summary' | 'done'
  data: Record<string, unknown>
}

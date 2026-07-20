import { cn, SEVERITY_CONFIG } from '@/lib/utils'

interface Props {
  severity: string
  size?: 'sm' | 'md' | 'lg'
}

export function SeverityBadge({ severity, size = 'md' }: Props) {
  const config = SEVERITY_CONFIG[severity.toLowerCase()] || SEVERITY_CONFIG.info
  return (
    <span className={cn(
      'inline-flex items-center font-semibold rounded-full border',
      config.color, config.bg, config.border,
      size === 'sm' && 'text-xs px-2 py-0.5',
      size === 'md' && 'text-sm px-2.5 py-1',
      size === 'lg' && 'text-base px-3 py-1.5',
    )}>
      {config.label}
    </span>
  )
}

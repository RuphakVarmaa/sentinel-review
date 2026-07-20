'use client'
import { useCallback } from 'react'
import CodeMirror from '@uiw/react-codemirror'
import { oneDark } from '@codemirror/theme-one-dark'

interface Props {
  value: string
  onChange: (v: string) => void
  readOnly?: boolean
}

export function DiffEditor({ value, onChange, readOnly = false }: Props) {
  const handleChange = useCallback((val: string) => onChange(val), [onChange])
  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <CodeMirror
        value={value}
        height="400px"
        theme={oneDark}
        readOnly={readOnly}
        onChange={handleChange}
        placeholder="Paste your unified diff here (git diff output)..."
        basicSetup={{
          lineNumbers: true,
          foldGutter: true,
          bracketMatching: true,
          highlightActiveLine: !readOnly,
        }}
      />
    </div>
  )
}

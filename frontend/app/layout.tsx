import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Providers } from '@/components/providers'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Sentinel Review — AI Code Review in Seconds',
  description: 'Instant AI-powered code review for GitHub PRs and diffs. Security, logic, performance, and style analysis in seconds.',
  openGraph: {
    title: 'Sentinel Review — AI Code Review in Seconds',
    description: 'Paste a diff, get instant AI review. Security vulnerabilities, logic bugs, performance issues, and more.',
    type: 'website',
  },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}

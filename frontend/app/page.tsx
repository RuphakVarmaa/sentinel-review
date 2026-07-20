import Link from 'next/link'
import { ArrowRight, Shield, Zap, Bug, Code2, Github, CheckCircle } from 'lucide-react'

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white">
      {/* Nav */}
      <nav className="border-b border-gray-100 px-6 py-4 flex items-center justify-between max-w-7xl mx-auto">
        <div className="flex items-center gap-2">
          <span className="text-2xl">🛡️</span>
          <span className="font-bold text-gray-900">Sentinel Review</span>
        </div>
        <div className="flex items-center gap-4">
          <Link href="/docs" className="text-sm text-gray-500 hover:text-gray-900">Docs</Link>
          <Link href="/review" className="text-sm text-gray-500 hover:text-gray-900">Review</Link>
          <Link
            href={`https://github.com/apps/${process.env.NEXT_PUBLIC_GITHUB_APP_SLUG || 'sentinel-review-app'}/installations/new`}
            className="bg-gray-900 text-white text-sm px-4 py-2 rounded-lg hover:bg-gray-700 flex items-center gap-2"
          >
            <Github className="h-4 w-4" />
            Install GitHub App
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="max-w-4xl mx-auto px-6 py-24 text-center">
        <div className="inline-flex items-center gap-2 bg-blue-50 text-blue-700 text-sm px-3 py-1 rounded-full mb-6">
          <span className="h-1.5 w-1.5 bg-blue-500 rounded-full" />
          Powered by GPT-4o
        </div>
        <h1 className="text-5xl md:text-6xl font-bold text-gray-900 leading-tight">
          AI Code Review<br />in Seconds
        </h1>
        <p className="mt-6 text-xl text-gray-500 max-w-2xl mx-auto">
          Instant security, logic, performance, and style analysis for every PR.
          Catch critical vulnerabilities before they reach production.
        </p>
        <div className="mt-8 flex items-center justify-center gap-4 flex-wrap">
          <Link
            href="/review"
            className="bg-gray-900 text-white px-6 py-3 rounded-lg text-base font-medium hover:bg-gray-700 flex items-center gap-2"
          >
            Try It Free <ArrowRight className="h-4 w-4" />
          </Link>
          <Link
            href={`https://github.com/apps/${process.env.NEXT_PUBLIC_GITHUB_APP_SLUG || 'sentinel-review-app'}/installations/new`}
            className="border border-gray-300 text-gray-700 px-6 py-3 rounded-lg text-base font-medium hover:bg-gray-50 flex items-center gap-2"
          >
            <Github className="h-4 w-4" />
            Install GitHub App
          </Link>
        </div>
      </section>

      {/* Stats ticker */}
      <div className="bg-gray-900 text-white py-4">
        <div className="max-w-7xl mx-auto px-6 flex items-center justify-center gap-8 flex-wrap text-sm">
          <div className="flex items-center gap-2">
            <CheckCircle className="h-4 w-4 text-green-400" />
            <span><strong>10,000+</strong> reviews run</span>
          </div>
          <div className="flex items-center gap-2">
            <Code2 className="h-4 w-4 text-blue-400" />
            <span><strong>500+</strong> repos protected</span>
          </div>
          <div className="flex items-center gap-2">
            <Shield className="h-4 w-4 text-red-400" />
            <span><strong>2,400+</strong> critical bugs caught</span>
          </div>
          <div className="flex items-center gap-2">
            <Zap className="h-4 w-4 text-yellow-400" />
            <span><strong>~8s</strong> average review time</span>
          </div>
        </div>
      </div>

      {/* Feature grid */}
      <section className="max-w-7xl mx-auto px-6 py-20">
        <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
          Five-layer code analysis
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[
            { icon: '🔒', title: 'Security Scan', desc: 'OWASP Top-10, SQL injection, hardcoded secrets, auth flaws, CWE references', color: 'red' },
            { icon: '🧠', title: 'Logic Bugs', desc: 'Off-by-one errors, null dereferences, race conditions, missing edge cases', color: 'purple' },
            { icon: '⚡', title: 'Performance', desc: 'N+1 queries, blocking I/O, memory leaks, unnecessary loops, missing indexes', color: 'yellow' },
            { icon: '🎨', title: 'Style & Quality', desc: 'Poor naming, code duplication, magic numbers, dead code, consistency issues', color: 'blue' },
            { icon: '🔧', title: 'Maintainability', desc: 'Tight coupling, missing abstractions, test coverage gaps, API documentation', color: 'green' },
            { icon: '📋', title: 'CI Integration', desc: 'Fails builds on critical issues, posts inline PR comments, GitHub App support', color: 'gray' },
          ].map(f => (
            <div key={f.title} className="border border-gray-200 rounded-xl p-6 hover:shadow-md transition-shadow">
              <div className="text-3xl mb-3">{f.icon}</div>
              <h3 className="font-semibold text-gray-900 mb-2">{f.title}</h3>
              <p className="text-sm text-gray-500">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Pricing */}
      <section className="bg-gray-50 py-20">
        <div className="max-w-4xl mx-auto px-6">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">Simple pricing</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white border border-gray-200 rounded-xl p-8">
              <div className="text-2xl font-bold text-gray-900">Free</div>
              <div className="text-gray-500 mt-1">5 reviews / day</div>
              <div className="mt-6 space-y-3 text-sm text-gray-600">
                {['5 public diff reviews/day', 'All analysis categories', 'Share review URLs', 'GitHub Actions CI'].map(f => (
                  <div key={f} className="flex items-center gap-2"><CheckCircle className="h-4 w-4 text-green-500" />{f}</div>
                ))}
              </div>
              <Link href="/review" className="mt-6 block text-center border border-gray-300 py-2 rounded-lg text-sm hover:bg-gray-50">
                Get started
              </Link>
            </div>
            <div className="bg-gray-900 text-white rounded-xl p-8">
              <div className="text-2xl font-bold">Pro</div>
              <div className="text-gray-400 mt-1">$9 / month</div>
              <div className="mt-6 space-y-3 text-sm text-gray-300">
                {['Unlimited reviews', 'GitHub App (auto-reviews)', 'Dashboard + history', 'API access', 'Priority support'].map(f => (
                  <div key={f} className="flex items-center gap-2"><CheckCircle className="h-4 w-4 text-green-400" />{f}</div>
                ))}
              </div>
              <button className="mt-6 w-full bg-white text-gray-900 py-2 rounded-lg text-sm font-medium hover:bg-gray-100">
                Upgrade to Pro
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-100 py-8 text-center text-sm text-gray-400">
        <p>© 2024 Sentinel Review · <Link href="/docs" className="hover:text-gray-600">Docs</Link> · <Link href="/review" className="hover:text-gray-600">Review Tool</Link></p>
      </footer>
    </div>
  )
}

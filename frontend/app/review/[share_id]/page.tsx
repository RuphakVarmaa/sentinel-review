import { getSharedReview } from '@/lib/api'
import { notFound } from 'next/navigation'
import Link from 'next/link'

export default async function SharedReviewPage({ params }: { params: { share_id: string } }) {
  const review = await getSharedReview(params.share_id)
  if (!review) notFound()

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2">
          <span className="text-xl">🛡️</span>
          <span className="font-bold text-gray-900 text-sm">Sentinel Review</span>
        </Link>
        <Link href="/review" className="text-sm bg-gray-900 text-white px-4 py-2 rounded-lg hover:bg-gray-700">
          Run your own review →
        </Link>
      </nav>
      <div className="max-w-3xl mx-auto px-6 py-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Shared Review</h1>
        <p className="text-gray-500 text-sm mb-6">
          Overall: <strong>{review.overall_severity}</strong> · {review.findings.length} findings · {review.model_used}
        </p>
        <div className="space-y-4">
          {review.findings.map((f, i) => (
            <div key={i} className="bg-white border border-gray-200 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-xs font-semibold uppercase text-red-600">{f.severity}</span>
                <span className="text-xs text-gray-400">{f.category}</span>
                {f.file_path && <code className="text-xs text-gray-400">{f.file_path}</code>}
              </div>
              <h3 className="font-semibold text-gray-900">{f.title}</h3>
              <p className="text-sm text-gray-600 mt-1">{f.explanation}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

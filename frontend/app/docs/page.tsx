import Link from 'next/link'

export default function DocsPage() {
  const workflowYaml = `name: Sentinel AI Code Review
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  ai-review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Get PR diff
        id: diff
        run: |
          git diff origin/\${{ github.base_ref }}...HEAD > pr.diff
          echo "lines=\$(wc -l < pr.diff)" >> \$GITHUB_OUTPUT

      - name: Run Sentinel Review
        id: review
        run: |
          RESPONSE=\$(curl -s -X POST \\
            -H "Authorization: Bearer \${{ secrets.SENTINEL_API_KEY }}" \\
            -H "Content-Type: application/json" \\
            -d "{\\"diff\\": \$(cat pr.diff | jq -Rs .), \\"context\\": \\"\${{ github.event.pull_request.title }}\\", \\"source\\": \\"ci\\"}" \\
            https://sentinel-review-api.railway.app/v1/review)
          echo "review_id=\$(echo \$RESPONSE | jq -r .review_id)" >> \$GITHUB_OUTPUT
          echo "severity=\$(echo \$RESPONSE | jq -r .overall_severity)" >> \$GITHUB_OUTPUT
          echo "critical=\$(echo \$RESPONSE | jq -r .finding_counts.critical)" >> \$GITHUB_OUTPUT
          echo "high=\$(echo \$RESPONSE | jq -r .finding_counts.high)" >> \$GITHUB_OUTPUT

      - name: Post PR Comment
        uses: actions/github-script@v7
        with:
          script: |
            const severity = '\${{ steps.review.outputs.severity }}';
            const critical = '\${{ steps.review.outputs.critical }}';
            const high = '\${{ steps.review.outputs.high }}';
            const reviewId = '\${{ steps.review.outputs.review_id }}';
            const emoji = {CRITICAL:'🚨',HIGH:'🔴',MEDIUM:'🟡',LOW:'🔵',PASS:'✅'}[severity];
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: \`## \${emoji} Sentinel AI Review: \${severity}\\n\\n\` +
                \`**\${critical} critical** · **\${high} high** issues found\\n\\n\` +
                \`[View full report](https://sentinel-review.vercel.app/review/\${reviewId})\`
            });

      - name: Fail on critical findings
        if: steps.review.outputs.critical > 0
        run: |
          echo "::error::Critical issues found. Review required."
          exit 1`

  return (
    <div className="min-h-screen bg-white">
      <nav className="border-b border-gray-100 px-6 py-4 flex items-center gap-4">
        <Link href="/" className="flex items-center gap-2">
          <span className="text-xl">🛡️</span>
          <span className="font-bold text-gray-900 text-sm">Sentinel Review</span>
        </Link>
        <span className="text-gray-300">/</span>
        <span className="text-sm text-gray-500">Docs</span>
      </nav>

      <div className="max-w-3xl mx-auto px-6 py-12 space-y-12">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Documentation</h1>
          <p className="mt-2 text-gray-500">Integrate Sentinel Review into your workflow in minutes.</p>
        </div>

        <section>
          <h2 className="text-xl font-bold text-gray-900 mb-4">GitHub Actions</h2>
          <p className="text-gray-500 mb-4 text-sm">
            Add this workflow to <code className="bg-gray-100 px-1.5 py-0.5 rounded">.github/workflows/sentinel-review.yml</code> in your repo.
            Set <code className="bg-gray-100 px-1.5 py-0.5 rounded">SENTINEL_API_KEY</code> in your repo secrets.
          </p>
          <pre className="bg-gray-900 text-green-300 text-xs p-4 rounded-xl overflow-x-auto">
            {workflowYaml}
          </pre>
        </section>

        <section>
          <h2 className="text-xl font-bold text-gray-900 mb-4">GitHub App</h2>
          <ol className="space-y-3 text-sm text-gray-600">
            <li className="flex gap-3"><span className="font-bold text-gray-900 w-6">1.</span> Click &quot;Install GitHub App&quot; on the homepage</li>
            <li className="flex gap-3"><span className="font-bold text-gray-900 w-6">2.</span> Select the repositories you want Sentinel to review</li>
            <li className="flex gap-3"><span className="font-bold text-gray-900 w-6">3.</span> Open or update a PR — Sentinel will automatically post a review</li>
          </ol>
        </section>

        <section>
          <h2 className="text-xl font-bold text-gray-900 mb-4">API Reference</h2>
          <p className="text-sm text-gray-500 mb-4">Base URL: <code className="bg-gray-100 px-1.5 py-0.5 rounded">https://sentinel-review-api.railway.app</code></p>
          <div className="space-y-4">
            <div className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <span className="bg-blue-100 text-blue-700 text-xs font-bold px-2 py-0.5 rounded">POST</span>
                <code className="text-sm">/v1/review</code>
              </div>
              <p className="text-sm text-gray-500">Submit a diff for review. Returns full findings JSON.</p>
              <pre className="mt-3 bg-gray-50 text-xs p-3 rounded">{`{
  "diff": "string (unified diff)",
  "context": "string (optional, PR description)",
  "source": "web|api|ci"
}`}</pre>
            </div>
            <div className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <span className="bg-blue-100 text-blue-700 text-xs font-bold px-2 py-0.5 rounded">POST</span>
                <code className="text-sm">/v1/review/stream</code>
              </div>
              <p className="text-sm text-gray-500">Same as above but streams SSE events. Suitable for UI integration.</p>
            </div>
            <div className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <span className="bg-green-100 text-green-700 text-xs font-bold px-2 py-0.5 rounded">GET</span>
                <code className="text-sm">/api/docs</code>
              </div>
              <p className="text-sm text-gray-500">Interactive OpenAPI documentation (Swagger UI).</p>
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}

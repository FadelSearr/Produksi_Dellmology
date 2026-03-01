'use client'

import { useEffect, useState } from 'react'

interface TopFeature {
  day_index: number
  feature: string
  importance: number
}

export default function XAIReport({ symbol, topK = 8 }: { symbol: string; topK?: number }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [explanation, setExplanation] = useState<any | null>(null)

  const fetchExplanation = async () => {
    setLoading(true)
    setError(null)
    try {
      const resp = await fetch('/api/xai', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbol, top_k: topK }),
      })
      const json = await resp.json()
      if (!json.success) throw new Error(json.error || 'XAI error')
      setExplanation(json.explanation)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    // load when component mounts
    fetchExplanation()
  }, [symbol])

  if (loading) return <div className="text-sm text-gray-400">Loading explanation…</div>
  if (error) return <div className="text-sm text-red-400">Error: {error}</div>
  if (!explanation) return null

  return (
    <div className="bg-gray-900/50 border border-gray-700 rounded p-3 text-sm">
      <div className="flex items-center justify-between mb-2">
        <div className="font-semibold">Model explanation</div>
        <div className="text-xs text-gray-400">Up prob: {(explanation.base_prob_up*100).toFixed(1)}%</div>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <div>
          <div className="text-xs text-gray-400 mb-1">Top contributors</div>
          <ul className="space-y-1">
            {explanation.top_features.map((t: TopFeature, i: number) => (
              <li key={i} className="flex justify-between">
                <span className="text-xs">{t.feature} (d-{t.day_index})</span>
                <span className="text-xs font-mono">{t.importance.toFixed(4)}</span>
              </li>
            ))}
          </ul>
        </div>

        <div>
          <div className="text-xs text-gray-400 mb-1">Aggregate feature importance</div>
          <ul className="space-y-1">
            {Object.entries(explanation.aggregate_feature_importance).map(([k, v]) => (
              <li key={k} className="flex justify-between">
                <span className="text-xs">{k}</span>
                <span className="text-xs font-mono">{(v as number).toFixed(4)}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  )
}

import { useEffect, useState } from 'react'
import { api } from '../lib/api.js'

export default function LearnPage() {
  const [patterns, setPatterns] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api.patterns()
      .then((data) => setPatterns(data.patterns))
      .catch((err) => setError(err.message))
  }, [])

  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="text-3xl font-extrabold">Common scams to watch for</h1>
      <p className="mt-2 text-lg text-slate-600">
        Scammers reuse the same tricks. Once you can recognize these patterns,
        they are much easier to spot.
      </p>

      {error && <p role="alert" className="mt-4 font-semibold text-red-700">{error}</p>}
      {patterns === null && !error && (
        <p className="card mt-6 animate-pulse text-slate-500">Loading…</p>
      )}

      <div className="mt-6 space-y-4">
        {patterns?.map((p) => (
          <article key={p.id} className="card">
            <h2 className="text-xl font-bold">{p.title}</h2>
            <blockquote className="mt-3 rounded-xl border-l-4 border-red-400 bg-red-50 p-4 text-slate-800 italic">
              “{p.example}”
            </blockquote>
            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <div>
                <h3 className="font-bold text-slate-700">How it works</h3>
                <p className="mt-1 text-slate-600">{p.how_it_works}</p>
              </div>
              <div>
                <h3 className="font-bold text-green-800">How to respond</h3>
                <p className="mt-1 text-slate-600">{p.how_to_respond}</p>
              </div>
            </div>
          </article>
        ))}
      </div>
    </div>
  )
}

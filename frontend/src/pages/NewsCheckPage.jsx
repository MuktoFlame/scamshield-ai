import { useState } from 'react'
import { api } from '../lib/api.js'
import ScanResult from '../components/ScanResult.jsx'
import Guidance from '../components/Guidance.jsx'

const VERDICT_STYLE = {
  supported: 'bg-green-100 text-green-800 border-green-300',
  refuted: 'bg-red-100 text-red-800 border-red-300',
  unverifiable: 'bg-slate-100 text-slate-700 border-slate-300',
}
const VERDICT_LABEL = {
  supported: '✓ Supported by references',
  refuted: '✗ Contradicted by references',
  unverifiable: '? Could not be verified',
}

export default function NewsCheckPage() {
  const [mode, setMode] = useState('text')
  const [text, setText] = useState('')
  const [url, setUrl] = useState('')
  const [language, setLanguage] = useState('en')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const submit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const body = mode === 'text'
        ? { text: text.trim(), language }
        : { url: url.trim(), language }
      setResult(await api.checkNews(body))
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const canSubmit = mode === 'text' ? text.trim().length >= 10 : url.trim().length >= 4

  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="text-3xl font-extrabold tracking-tight">Check news & facts</h1>
      <p className="mt-2 text-lg text-slate-600">
        Paste an article, a headline, or a claim someone shared. We analyze
        how it's written and check its main claims against reference sources
        — with citations you can read yourself.
      </p>

      <form onSubmit={submit} className="card mt-6">
        <div className="flex gap-2" role="tablist" aria-label="Input type">
          <button type="button" role="tab" aria-selected={mode === 'text'}
            className={`btn-secondary text-sm ${mode === 'text' ? '!border-blue-600 !text-blue-700' : ''}`}
            onClick={() => setMode('text')}>
            Paste text
          </button>
          <button type="button" role="tab" aria-selected={mode === 'url'}
            className={`btn-secondary text-sm ${mode === 'url' ? '!border-blue-600 !text-blue-700' : ''}`}
            onClick={() => setMode('url')}>
            Article link
          </button>
        </div>

        {mode === 'text' ? (
          <div className="mt-4">
            <label htmlFor="newstext" className="label">The article, headline, or claim</label>
            <textarea id="newstext" className="input min-h-40"
              placeholder="Paste the story or claim you want checked…"
              value={text} onChange={(e) => setText(e.target.value)}
              maxLength={20000} />
          </div>
        ) : (
          <div className="mt-4">
            <label htmlFor="newsurl" className="label">Link to the article</label>
            <input id="newsurl" className="input font-mono"
              placeholder="https://example.com/article"
              value={url} onChange={(e) => setUrl(e.target.value)}
              maxLength={2000} />
          </div>
        )}

        <div className="mt-4 flex flex-wrap items-end gap-4">
          <div>
            <label htmlFor="language" className="label">Explain in</label>
            <select id="language" className="input !w-auto" value={language}
              onChange={(e) => setLanguage(e.target.value)}>
              <option value="en">English</option>
              <option value="bn">বাংলা (Bangla)</option>
            </select>
          </div>
          <button type="submit" className="btn-primary ms-auto"
            disabled={loading || !canSubmit}>
            {loading ? 'Checking…' : 'Check it'}
          </button>
        </div>
      </form>

      {error && (
        <div role="alert" className="card mt-6 border-2 border-red-300 bg-red-50 text-red-900">
          <p className="font-semibold">Could not run the check</p>
          <p>{error}</p>
        </div>
      )}
      {loading && (
        <div className="card mt-6 animate-pulse text-center text-lg text-slate-500">
          Analyzing the writing and checking claims against references…
        </div>
      )}

      {result && (
        <div className="mt-6 space-y-4">
          {result.title && (
            <p className="text-slate-600">Article: <strong>{result.title}</strong></p>
          )}
          <ScanResult result={result} />

          {result.claims?.length > 0 && (
            <section className="card">
              <h3 className="text-lg font-bold">Fact-check of the main claims</h3>
              <ul className="mt-3 space-y-3">
                {result.claims.map((c, i) => (
                  <li key={i} className={`rounded-xl border-2 p-4 ${VERDICT_STYLE[c.verdict]}`}>
                    <p className="font-semibold">“{c.claim}”</p>
                    <p className="mt-1 font-bold">{VERDICT_LABEL[c.verdict]}</p>
                    <p className="mt-1">{c.rationale}</p>
                    {c.sources?.length > 0 && (
                      <p className="mt-2 text-sm">
                        Sources:{' '}
                        {c.sources.map((s, j) => (
                          <span key={j}>
                            {j > 0 && ' · '}
                            <a href={s.url} target="_blank" rel="noreferrer"
                              className="font-semibold underline">
                              {s.title}
                            </a>
                          </span>
                        ))}
                      </p>
                    )}
                  </li>
                ))}
              </ul>
            </section>
          )}

          {typeof result.style_score === 'number' && (
            <p className="text-sm text-slate-500">
              Writing-style analysis: {Math.round(result.style_score * 100)}%
              similarity to known misinformation style (style is a warning
              sign, not a verdict — that's why claims are checked separately).
            </p>
          )}
          <Guidance items={result.guidance} />
        </div>
      )}
    </div>
  )
}

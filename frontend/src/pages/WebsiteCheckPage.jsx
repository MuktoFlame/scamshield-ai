import { useState } from 'react'
import { api } from '../lib/api.js'
import ScanResult from '../components/ScanResult.jsx'
import Guidance from '../components/Guidance.jsx'

export default function WebsiteCheckPage() {
  const [url, setUrl] = useState('')
  const [language, setLanguage] = useState('en')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const submit = async (e) => {
    e.preventDefault()
    if (!url.trim()) return
    setLoading(true)
    setError('')
    setResult(null)
    try {
      setResult(await api.checkUrl({ url: url.trim(), language }))
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="text-3xl font-extrabold tracking-tight">Check a website</h1>
      <p className="mt-2 text-lg text-slate-600">
        Paste a link before you click it. We analyze the address, run it
        through a model trained on 60,000 phishing sites, and visit the page
        safely so you don't have to.
      </p>

      <form onSubmit={submit} className="card mt-6">
        <label htmlFor="url" className="label">The web address (link)</label>
        <input
          id="url"
          className="input font-mono"
          placeholder="e.g. secure-verify-account.com/login"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          maxLength={2000}
        />
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
            disabled={loading || !url.trim()}>
            {loading ? 'Checking…' : 'Check this link'}
          </button>
        </div>
      </form>

      {error && (
        <div role="alert" className="card mt-6 border-2 border-red-300 bg-red-50 text-red-900">
          <p className="font-semibold">Could not check that address</p>
          <p>{error}</p>
        </div>
      )}
      {loading && (
        <div className="card mt-6 animate-pulse text-center text-lg text-slate-500">
          Inspecting the address and visiting the page safely…
        </div>
      )}

      {result && (
        <div className="mt-6 space-y-4">
          <div className="card !py-4 text-slate-600">
            <span className="font-semibold text-slate-800">{result.domain}</span>
            {result.known_site && (
              <span className="ms-2 rounded-full bg-green-100 px-3 py-0.5 text-sm font-semibold text-green-800">
                ✓ well-known website
              </span>
            )}
            {result.fetched
              ? <span className="ms-2 text-sm">page visited safely</span>
              : <span className="ms-2 text-sm">page could not be loaded{result.fetch_note ? ` — ${result.fetch_note}` : ''}</span>}
          </div>
          <ScanResult result={result} />
          <Guidance items={result.guidance} />
        </div>
      )}
    </div>
  )
}

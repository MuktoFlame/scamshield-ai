import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../lib/api.js'
import { useAuth } from '../lib/auth.jsx'
import ScanResult from '../components/ScanResult.jsx'

const BADGES = {
  high: 'bg-red-600 text-white',
  medium: 'bg-amber-500 text-white',
  low: 'bg-green-600 text-white',
}

const TYPES = {
  message: { icon: '💬', label: 'Message' },
  url: { icon: '🔗', label: 'Website' },
  news: { icon: '📰', label: 'News' },
  product: { icon: '🛒', label: 'Product' },
}

export function ScanList({ scans }) {
  const [openId, setOpenId] = useState(null)

  if (scans.length === 0) {
    return <p className="card mt-6 text-lg text-slate-600">No checks yet.</p>
  }

  return (
    <ul className="mt-6 space-y-3">
      {scans.map((scan) => {
        const type = TYPES[scan.type] ?? TYPES.message
        return (
          <li key={scan.id} className="card !p-0">
            <button
              className="flex w-full flex-wrap items-center gap-3 p-4 text-left"
              onClick={() => setOpenId(openId === scan.id ? null : scan.id)}
              aria-expanded={openId === scan.id}
            >
              <span title={type.label} aria-label={type.label}>{type.icon}</span>
              <span className={`rounded-full px-3 py-0.5 text-sm font-bold uppercase ${BADGES[scan.result.risk_level]}`}>
                {scan.result.risk_level}
              </span>
              <span className="min-w-0 flex-1 truncate text-slate-700">{scan.text}</span>
              <span className="text-sm text-slate-500">
                {new Date(scan.created_at).toLocaleString()}
              </span>
            </button>
            {openId === scan.id && (
              <div className="border-t border-slate-200 p-4">
                <p className="mb-4 rounded-xl bg-slate-100 p-4 whitespace-pre-wrap">{scan.text}</p>
                <ScanResult result={scan.result} />
              </div>
            )}
          </li>
        )
      })}
    </ul>
  )
}

export default function HistoryPage() {
  const { user } = useAuth()
  const [scans, setScans] = useState(null)
  const [filter, setFilter] = useState('all')
  const [error, setError] = useState('')

  useEffect(() => {
    if (!user) return
    api.history()
      .then((data) => setScans(data.scans))
      .catch((err) => setError(err.message))
  }, [user])

  if (!user) {
    return (
      <p className="card mx-auto max-w-md text-center text-lg">
        <Link to="/login" className="font-semibold text-blue-700 underline">Sign in</Link>{' '}
        to see your scan history.
      </p>
    )
  }

  const visible = scans?.filter((s) => filter === 'all' || s.type === filter)

  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="text-3xl font-extrabold">My history</h1>
      <p className="mt-2 text-lg text-slate-600">
        Everything you have checked while signed in. Click one to see the full result.
      </p>

      <div className="mt-4 flex flex-wrap gap-2" role="group" aria-label="Filter by type">
        {[['all', '🗂 All'], ...Object.entries(TYPES).map(([k, v]) => [k, `${v.icon} ${v.label}`])].map(([key, label]) => (
          <button key={key}
            className={`btn-secondary !py-1.5 text-sm ${filter === key ? '!border-blue-600 !bg-blue-50 !text-blue-700' : ''}`}
            aria-pressed={filter === key}
            onClick={() => setFilter(key)}>
            {label}
          </button>
        ))}
      </div>

      {error && <p role="alert" className="mt-4 font-semibold text-red-700">{error}</p>}
      {scans === null && !error
        ? <p className="card mt-6 animate-pulse text-slate-500">Loading…</p>
        : visible && <ScanList scans={visible} />}
    </div>
  )
}

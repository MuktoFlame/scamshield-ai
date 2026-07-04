import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../lib/api.js'
import { useAuth } from '../lib/auth.jsx'
import { ScanList } from './HistoryPage.jsx'

function SeniorView() {
  const [code, setCode] = useState(null)
  const [error, setError] = useState('')

  const generate = async () => {
    setError('')
    try {
      setCode(await api.createLinkCode())
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div className="card mt-6">
      <h2 className="text-xl font-bold">Invite a family member</h2>
      <p className="mt-1 text-slate-600">
        Generate a code and read it to a family member with a caregiver
        account. They enter it on their Family page and can then see your scam
        checks — nothing else.
      </p>
      {code ? (
        <div className="mt-4 rounded-xl border-2 border-blue-300 bg-blue-50 p-5 text-center">
          <p className="text-slate-600">Your code (valid for {code.expires_in_minutes} minutes):</p>
          <p className="mt-1 font-mono text-5xl font-bold tracking-[0.3em] text-blue-900">
            {code.code}
          </p>
        </div>
      ) : (
        <button className="btn-primary mt-4" onClick={generate}>Generate invite code</button>
      )}
      {error && <p role="alert" className="mt-3 font-semibold text-red-700">{error}</p>}
    </div>
  )
}

function CaregiverView({ links, refresh }) {
  const [code, setCode] = useState('')
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [selected, setSelected] = useState(null)
  const [scans, setScans] = useState(null)

  const redeem = async (e) => {
    e.preventDefault()
    setError('')
    setMessage('')
    try {
      const data = await api.redeemLinkCode(code)
      setMessage(`Linked to ${data.senior.name}. You can now view their checks.`)
      setCode('')
      refresh()
    } catch (err) {
      setError(err.message)
    }
  }

  const view = async (senior) => {
    setSelected(senior)
    setScans(null)
    try {
      const data = await api.linkedHistory(senior.id)
      setScans(data.scans)
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <>
      <div className="card mt-6">
        <h2 className="text-xl font-bold">Link to a family member</h2>
        <p className="mt-1 text-slate-600">
          Ask them to generate an invite code on their Family page, then enter it here.
        </p>
        <form onSubmit={redeem} className="mt-4 flex flex-wrap items-center gap-3">
          <input
            className="input !w-44 text-center font-mono text-2xl tracking-widest"
            value={code}
            onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
            placeholder="000000"
            inputMode="numeric"
            aria-label="Six-digit invite code"
          />
          <button type="submit" className="btn-primary" disabled={code.length !== 6}>
            Link account
          </button>
        </form>
        {message && <p className="mt-3 font-semibold text-green-700">{message}</p>}
        {error && <p role="alert" className="mt-3 font-semibold text-red-700">{error}</p>}
      </div>

      {links.length > 0 && (
        <div className="mt-6">
          <h2 className="text-xl font-bold">People you help protect</h2>
          <div className="mt-3 flex flex-wrap gap-3">
            {links.map((link) => (
              <button
                key={link.id}
                className={`btn-secondary ${selected?.id === link.id ? '!border-blue-600 !text-blue-700' : ''}`}
                onClick={() => view(link)}
              >
                👤 {link.name}
              </button>
            ))}
          </div>
          {selected && (
            <div className="mt-4">
              <h3 className="text-lg font-bold">{selected.name}'s recent checks</h3>
              {scans === null
                ? <p className="card mt-3 animate-pulse text-slate-500">Loading…</p>
                : <ScanList scans={scans} />}
            </div>
          )}
        </div>
      )}
    </>
  )
}

export default function FamilyPage() {
  const { user } = useAuth()
  const [links, setLinks] = useState([])

  const refresh = useCallback(() => {
    if (user) api.myLinks().then((data) => setLinks(data.links)).catch(() => {})
  }, [user])

  useEffect(() => {
    refresh()
  }, [refresh])

  if (!user) {
    return (
      <p className="card mx-auto max-w-md text-center text-lg">
        <Link to="/login" className="font-semibold text-blue-700 underline">Sign in</Link>{' '}
        to use family protection.
      </p>
    )
  }

  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="text-3xl font-extrabold">Family protection</h1>
      <p className="mt-2 text-lg text-slate-600">
        {user.role === 'senior'
          ? 'Let someone you trust keep an eye out for scams with you.'
          : 'Review the scam checks of family members who invited you.'}
      </p>

      {user.role === 'senior' ? <SeniorView /> : <CaregiverView links={links} refresh={refresh} />}

      {user.role === 'senior' && links.length > 0 && (
        <div className="card mt-6">
          <h2 className="text-xl font-bold">Watching out for you</h2>
          <ul className="mt-2 space-y-1 text-lg">
            {links.map((link) => <li key={link.id}>👤 {link.name}</li>)}
          </ul>
        </div>
      )}
    </div>
  )
}

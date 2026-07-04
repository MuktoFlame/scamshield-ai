import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../lib/api.js'
import { useAuth } from '../lib/auth.jsx'

export default function RegisterPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ name: '', email: '', password: '', role: 'senior' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value })

  const submit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const data = await api.register(form)
      login(data.token, data.user)
      navigate('/')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto max-w-md">
      <h1 className="text-3xl font-extrabold">Create your account</h1>
      <form onSubmit={submit} className="card mt-6 space-y-4">
        <div>
          <label htmlFor="name" className="label">Your name</label>
          <input id="name" className="input" value={form.name}
            onChange={set('name')} required autoComplete="name" />
        </div>
        <div>
          <label htmlFor="email" className="label">Email</label>
          <input id="email" type="email" className="input" value={form.email}
            onChange={set('email')} required autoComplete="email" />
        </div>
        <div>
          <label htmlFor="password" className="label">Password (at least 8 characters)</label>
          <input id="password" type="password" className="input" value={form.password}
            onChange={set('password')} required minLength={8} autoComplete="new-password" />
        </div>
        <fieldset>
          <legend className="label">I am…</legend>
          <div className="space-y-2">
            <label className="flex cursor-pointer items-start gap-3 rounded-xl border-2 border-slate-200 p-3 has-checked:border-blue-600 has-checked:bg-blue-50">
              <input type="radio" name="role" value="senior" className="mt-1.5 h-5 w-5"
                checked={form.role === 'senior'} onChange={set('role')} />
              <span>
                <span className="font-semibold">Checking messages for myself</span>
                <br />
                <span className="text-sm text-slate-600">
                  You can invite a family member to help watch for scams.
                </span>
              </span>
            </label>
            <label className="flex cursor-pointer items-start gap-3 rounded-xl border-2 border-slate-200 p-3 has-checked:border-blue-600 has-checked:bg-blue-50">
              <input type="radio" name="role" value="caregiver" className="mt-1.5 h-5 w-5"
                checked={form.role === 'caregiver'} onChange={set('role')} />
              <span>
                <span className="font-semibold">Helping a family member stay safe</span>
                <br />
                <span className="text-sm text-slate-600">
                  You can link to their account and review their scam checks.
                </span>
              </span>
            </label>
          </div>
        </fieldset>
        {error && <p role="alert" className="font-semibold text-red-700">{error}</p>}
        <button type="submit" className="btn-primary w-full" disabled={loading}>
          {loading ? 'Creating account…' : 'Create account'}
        </button>
        <p className="text-center text-slate-600">
          Already have an account?{' '}
          <Link to="/login" className="font-semibold text-blue-700 underline">Sign in</Link>
        </p>
      </form>
    </div>
  )
}

import { useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../lib/api.js'
import { useAuth } from '../lib/auth.jsx'
import ScanResult from '../components/ScanResult.jsx'
import Guidance from '../components/Guidance.jsx'

const CHANNELS = [
  { value: 'sms', label: 'Text message (SMS)' },
  { value: 'email', label: 'Email' },
  { value: 'call', label: 'Phone call (what they said)' },
  { value: 'chat', label: 'WhatsApp / Messenger' },
  { value: 'other', label: 'Something else' },
]

const EXAMPLE =
  'URGENT: Your bank account has been locked due to suspicious activity. ' +
  'Verify your identity immediately at secure-verify-bank.com or your ' +
  'account will be permanently closed.'

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result.split(',')[1])
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

export default function ScanPage() {
  const { user } = useAuth()
  const fileInput = useRef(null)
  const [text, setText] = useState('')
  const [channel, setChannel] = useState('sms')
  const [language, setLanguage] = useState('en')
  const [result, setResult] = useState(null)
  const [extractedText, setExtractedText] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const submit = async (e) => {
    e.preventDefault()
    if (!text.trim()) return
    setLoading(true)
    setError('')
    setResult(null)
    setExtractedText(null)
    try {
      setResult(await api.scan({ text, channel, language }))
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const uploadScreenshot = async (e) => {
    const file = e.target.files?.[0]
    e.target.value = ''
    if (!file) return
    if (file.size > 6 * 1024 * 1024) {
      setError('That image is too large (max 6 MB).')
      return
    }
    setLoading(true)
    setError('')
    setResult(null)
    setExtractedText(null)
    try {
      const image_b64 = await fileToBase64(file)
      const data = await api.scanImage({
        image_b64,
        mime_type: file.type === 'image/jpg' ? 'image/jpeg' : file.type,
        channel,
        language,
      })
      setResult(data)
      setExtractedText(data.extracted_text)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="text-3xl font-extrabold tracking-tight">
        Got a suspicious message?
      </h1>
      <p className="mt-2 text-lg text-slate-600">
        Paste it below — or upload a screenshot — and we will check it for the
        warning signs scammers use. You do not need an account.
      </p>

      <form onSubmit={submit} className="card mt-6">
        <label htmlFor="message" className="label">
          The message you received
        </label>
        <textarea
          id="message"
          className="input min-h-44 font-normal"
          placeholder="Paste the text message, email, or what the caller said…"
          value={text}
          onChange={(e) => setText(e.target.value)}
          maxLength={10000}
        />

        <div className="mt-4 flex flex-wrap items-end gap-x-4 gap-y-3">
          <div>
            <label htmlFor="channel" className="label">How did it arrive?</label>
            <select
              id="channel"
              className="input !w-auto"
              value={channel}
              onChange={(e) => setChannel(e.target.value)}
            >
              {CHANNELS.map((c) => (
                <option key={c.value} value={c.value}>{c.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="language" className="label">Explain in</label>
            <select
              id="language"
              className="input !w-auto"
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
            >
              <option value="en">English</option>
              <option value="bn">বাংলা (Bangla)</option>
            </select>
          </div>
          <button type="submit" className="btn-primary ms-auto" disabled={loading || !text.trim()}>
            {loading ? 'Checking…' : 'Check this message'}
          </button>
        </div>

        <div className="mt-4 flex flex-wrap items-center gap-4 border-t border-slate-200 pt-3">
          <button
            type="button"
            className="btn-secondary text-sm"
            onClick={() => fileInput.current?.click()}
            disabled={loading}
          >
            📷 Upload a screenshot instead
          </button>
          <input
            ref={fileInput}
            type="file"
            accept="image/png,image/jpeg,image/webp"
            className="hidden"
            onChange={uploadScreenshot}
            aria-label="Upload a screenshot of the message"
          />
          <button
            type="button"
            className="text-sm font-semibold text-blue-700 underline"
            onClick={() => setText(EXAMPLE)}
          >
            Try an example scam message
          </button>
        </div>
      </form>

      {error && (
        <div role="alert" className="card mt-6 border-2 border-red-300 bg-red-50 text-red-900">
          <p className="font-semibold">Something went wrong</p>
          <p>{error}</p>
        </div>
      )}

      {loading && (
        <div className="card mt-6 animate-pulse text-center text-lg text-slate-500">
          Analyzing the message…
        </div>
      )}

      {result && (
        <div className="mt-6 space-y-4">
          {extractedText && (
            <div className="card">
              <h3 className="font-bold text-slate-700">Text we read from your screenshot</h3>
              <p className="mt-2 rounded-xl bg-slate-100 p-4 whitespace-pre-wrap">{extractedText}</p>
            </div>
          )}
          <ScanResult result={result} />
          <Guidance items={result.guidance} />
          {!user && (
            <p className="text-center text-slate-600">
              <Link to="/register" className="font-semibold text-blue-700 underline">
                Create a free account
              </Link>{' '}
              to keep a history of your checks and let a family member help watch for scams.
            </p>
          )}
        </div>
      )}
    </div>
  )
}

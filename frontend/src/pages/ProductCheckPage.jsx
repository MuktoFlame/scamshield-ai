import { useState } from 'react'
import { api } from '../lib/api.js'
import ScanResult from '../components/ScanResult.jsx'
import Guidance from '../components/Guidance.jsx'

export default function ProductCheckPage() {
  const [form, setForm] = useState({
    title: '', price: '', platform: '', description: '',
    seller_info: '', reviews_text: '', language: 'en',
  })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value })

  const submit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    setResult(null)
    try {
      setResult(await api.checkProduct(form))
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="text-3xl font-extrabold tracking-tight">Check a product listing</h1>
      <p className="mt-2 text-lg text-slate-600">
        Found a deal that seems too good? Fill in what you see in the listing —
        only the product name is required.
      </p>

      <form onSubmit={submit} className="card mt-6 space-y-4">
        <div>
          <label htmlFor="title" className="label">Product title (as listed) *</label>
          <input id="title" className="input" required maxLength={300}
            placeholder='e.g. "Brand New iPhone 15 Pro Max 256GB sealed"'
            value={form.title} onChange={set('title')} />
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label htmlFor="price" className="label">Price</label>
            <input id="price" className="input" maxLength={50}
              placeholder="e.g. $120 or Tk 9,500"
              value={form.price} onChange={set('price')} />
          </div>
          <div>
            <label htmlFor="platform" className="label">Where is it listed?</label>
            <input id="platform" className="input" maxLength={100}
              placeholder="e.g. Facebook Marketplace, Daraz, eBay"
              value={form.platform} onChange={set('platform')} />
          </div>
        </div>
        <div>
          <label htmlFor="description" className="label">Listing description</label>
          <textarea id="description" className="input min-h-28" maxLength={10000}
            placeholder="Copy the description text here…"
            value={form.description} onChange={set('description')} />
        </div>
        <div>
          <label htmlFor="seller" className="label">About the seller (optional)</label>
          <input id="seller" className="input" maxLength={1000}
            placeholder="e.g. account created last week, asks to pay by bKash directly"
            value={form.seller_info} onChange={set('seller_info')} />
        </div>
        <div>
          <label htmlFor="reviews" className="label">Paste a few reviews (optional)</label>
          <textarea id="reviews" className="input min-h-20" maxLength={10000}
            placeholder="Paste some of the product reviews here…"
            value={form.reviews_text} onChange={set('reviews_text')} />
        </div>
        <div className="flex flex-wrap items-end gap-4">
          <div>
            <label htmlFor="language" className="label">Explain in</label>
            <select id="language" className="input !w-auto" value={form.language}
              onChange={set('language')}>
              <option value="en">English</option>
              <option value="bn">বাংলা (Bangla)</option>
            </select>
          </div>
          <button type="submit" className="btn-primary ms-auto"
            disabled={loading || form.title.trim().length < 3}>
            {loading ? 'Checking…' : 'Check this listing'}
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
          Assessing the listing…
        </div>
      )}

      {result && (
        <div className="mt-6 space-y-4">
          <ScanResult result={result} />
          <Guidance items={result.guidance} />
        </div>
      )}
    </div>
  )
}

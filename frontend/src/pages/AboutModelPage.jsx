import { useEffect, useState } from 'react'
import { api } from '../lib/api.js'

function Stat({ label, value }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 text-center">
      <p className="text-3xl font-extrabold text-blue-800">{value}</p>
      <p className="mt-1 text-sm font-semibold text-slate-500">{label}</p>
    </div>
  )
}

function ModelCard({ name, info }) {
  if (!info?.available) return null
  return (
    <section className="card">
      <h3 className="text-xl font-bold">{name}</h3>
      <p className="mt-1 text-sm text-slate-500">
        {info.model} · trained {info.trained_on} ·{' '}
        {info.dataset?.total?.toLocaleString()} samples
        ({info.dataset?.sources?.join(', ')})
      </p>
      <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Stat label="Accuracy" value={`${(info.accuracy * 100).toFixed(1)}%`} />
        <Stat label="Precision" value={`${(info.precision * 100).toFixed(1)}%`} />
        <Stat label="Recall" value={`${(info.recall * 100).toFixed(1)}%`} />
        <Stat label="F1 score" value={info.f1?.toFixed(3)} />
      </div>
    </section>
  )
}

export default function AboutModelPage() {
  const [info, setInfo] = useState(null)

  useEffect(() => {
    api.modelInfo().then(setInfo).catch(() => setInfo({ available: false }))
  }, [])

  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="text-3xl font-extrabold">How the AI works</h1>
      <p className="mt-2 text-lg text-slate-600">
        Every check combines several independent layers, so no single
        component has to be trusted blindly — and the language model never
        decides a verdict, it only explains one.
      </p>

      <ol className="mt-6 space-y-4">
        <li className="card">
          <h2 className="text-lg font-bold">1. Rule engines with visible evidence</h2>
          <p className="mt-1 text-slate-600">
            Deterministic rules look for known scam ingredients — urgency
            pressure, gift-card demands, lookalike web addresses, off-platform
            payment requests. Every rule that fires shows you the exact text
            it matched.
          </p>
        </li>
        <li className="card">
          <h2 className="text-lg font-bold">2. Three trained machine-learning models</h2>
          <p className="mt-1 text-slate-600">
            Separate classifiers for scam messages, phishing web addresses,
            and misinformation writing style, trained on public research
            datasets. Their measured performance is shown below — live from
            the server, not copied into this page.
          </p>
        </li>
        <li className="card">
          <h2 className="text-lg font-bold">3. Retrieval-augmented fact checking (RAG)</h2>
          <p className="mt-1 text-slate-600">
            For news and claims, the system extracts the main factual claims,
            retrieves relevant reference passages from Wikipedia using BM25
            ranking, and judges each claim strictly against that evidence —
            with sources you can open yourself. A separate retrieval layer
            attaches curated safety guidance to every result.
          </p>
        </li>
        <li className="card">
          <h2 className="text-lg font-bold">4. A language model that explains</h2>
          <p className="mt-1 text-slate-600">
            Google Gemini turns the technical findings into plain English or
            Bangla and a concrete next step. It is given the verdict as fixed
            ground truth. If it is unavailable, a built-in explainer takes
            over — a check never fails because the AI service did.
          </p>
        </li>
      </ol>

      <h2 className="mt-8 text-2xl font-bold">Measured model performance</h2>
      <p className="mt-1 mb-4 text-slate-600">
        On held-out test sets never seen during training:
      </p>
      <div className="space-y-4">
        <ModelCard name="💬 Scam message classifier" info={info?.models?.message ?? info} />
        <ModelCard name="🔗 Phishing URL classifier" info={info?.models?.url} />
        <ModelCard name="📰 Misinformation style classifier" info={info?.models?.news} />
      </div>
    </div>
  )
}

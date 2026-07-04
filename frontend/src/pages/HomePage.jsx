import { Link } from 'react-router-dom'

const CHECKERS = [
  {
    to: '/check/message',
    icon: '💬',
    title: 'Check a message',
    text: 'Paste a suspicious SMS, email, or what a caller said — or upload a screenshot.',
  },
  {
    to: '/check/website',
    icon: '🔗',
    title: 'Check a website',
    text: 'Paste a link before you click it. We inspect the address and visit the page safely for you.',
  },
  {
    to: '/check/news',
    icon: '📰',
    title: 'Check news & facts',
    text: 'Paste an article, headline, or claim. We analyze the writing style and verify the facts against references.',
  },
  {
    to: '/check/product',
    icon: '🛒',
    title: 'Check a product listing',
    text: 'Too-good-to-be-true deal? We assess the price, the seller, and the wording for fraud signs.',
  },
]

export default function HomePage() {
  return (
    <div className="mx-auto max-w-4xl">
      <div className="text-center">
        <h1 className="text-4xl font-extrabold tracking-tight">
          What would you like to check?
        </h1>
        <p className="mx-auto mt-3 max-w-2xl text-lg text-slate-600">
          ScamShield AI checks messages, links, news, and shopping deals for
          the tricks scammers use — and explains what it finds in plain
          language. Free, no account needed.
        </p>
      </div>

      <div className="mt-8 grid gap-4 sm:grid-cols-2">
        {CHECKERS.map((c) => (
          <Link
            key={c.to}
            to={c.to}
            className="card group border-2 transition hover:border-blue-500 hover:shadow-md focus-visible:outline-4 focus-visible:outline-blue-300"
          >
            <span aria-hidden="true" className="text-4xl">{c.icon}</span>
            <h2 className="mt-3 text-xl font-bold group-hover:text-blue-800">
              {c.title} →
            </h2>
            <p className="mt-1 text-slate-600">{c.text}</p>
          </Link>
        ))}
      </div>

      <p className="mt-8 text-center text-slate-500">
        Powered by three trained machine-learning models, a rule engine with
        evidence you can see, and AI fact-checking with cited sources.{' '}
        <Link to="/about-model" className="font-semibold text-blue-700 underline">
          How it works
        </Link>
      </p>
    </div>
  )
}

const LEVELS = {
  high: {
    label: 'High risk — very likely a scam',
    icon: '🚫',
    wrap: 'border-red-300 bg-red-50',
    badge: 'bg-red-600 text-white',
    bar: 'bg-red-600',
  },
  medium: {
    label: 'Medium risk — be careful',
    icon: '⚠️',
    wrap: 'border-amber-300 bg-amber-50',
    badge: 'bg-amber-500 text-white',
    bar: 'bg-amber-500',
  },
  low: {
    label: 'Low risk — no strong warning signs',
    icon: '✅',
    wrap: 'border-green-300 bg-green-50',
    badge: 'bg-green-600 text-white',
    bar: 'bg-green-600',
  },
}

export default function ScanResult({ result }) {
  const level = LEVELS[result.risk_level] ?? LEVELS.low
  const pct = Math.round(result.risk_score * 100)

  return (
    <section aria-live="polite" className={`card border-2 ${level.wrap}`}>
      <div className="flex flex-wrap items-center gap-3">
        <span aria-hidden="true" className="text-4xl">{level.icon}</span>
        <div>
          <span className={`inline-block rounded-full px-4 py-1 text-lg font-bold ${level.badge}`}>
            {level.label}
          </span>
          <p className="mt-1 text-sm text-slate-600">
            Risk score {pct}/100
            {result.explanation_source === 'llm'
              ? ' · explained by AI'
              : ' · explained by rule analysis'}
          </p>
        </div>
      </div>

      <div className="mt-4 h-3 w-full overflow-hidden rounded-full bg-white" role="img"
        aria-label={`Risk score ${pct} out of 100`}>
        <div className={`h-full rounded-full ${level.bar}`} style={{ width: `${pct}%` }} />
      </div>

      <p className="mt-5 text-lg leading-relaxed">{result.summary}</p>

      <div className="mt-4 rounded-xl border-2 border-blue-200 bg-blue-50 p-4">
        <h3 className="font-bold text-blue-900">What you should do</h3>
        <p className="mt-1 text-lg leading-relaxed text-blue-950">
          {result.recommended_action}
        </p>
      </div>

      {result.flags?.length > 0 && (
        <div className="mt-5">
          <h3 className="mb-2 text-lg font-bold">Warning signs we found</h3>
          <ul className="space-y-3">
            {result.flags.map((flag) => (
              <li key={flag.id} className="rounded-xl border border-slate-200 bg-white p-4">
                <p className="font-semibold">{flag.title}</p>
                <p className="mt-0.5 text-slate-600">{flag.description}</p>
                {flag.evidence?.length > 0 && (
                  <p className="mt-2 text-sm text-slate-500">
                    Found in the message:{' '}
                    {flag.evidence.map((e, i) => (
                      <span key={i}>
                        {i > 0 && ', '}
                        <mark className="rounded bg-yellow-100 px-1 font-medium">{e}</mark>
                      </span>
                    ))}
                  </p>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  )
}

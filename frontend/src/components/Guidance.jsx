export default function Guidance({ items }) {
  if (!items?.length) return null
  return (
    <section className="card">
      <h3 className="text-lg font-bold">📚 Learn more</h3>
      <ul className="mt-3 space-y-3">
        {items.map((g, i) => (
          <li key={i} className="rounded-xl border border-slate-200 bg-slate-50 p-4">
            <p className="font-semibold text-slate-800">{g.title}</p>
            <p className="mt-1 text-slate-600">{g.snippet}</p>
          </li>
        ))}
      </ul>
    </section>
  )
}

export function EmptyState() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center rounded-xl border border-dashed border-slate-300 bg-white/60 px-6 py-20 text-center">
      <div className="text-4xl">🔍</div>
      <h2 className="mt-4 text-lg font-semibold text-slate-700">Research a company before your next meeting</h2>
      <p className="mt-2 max-w-sm text-sm text-slate-500">
        Type a company name above and hit Enter. You'll get a 5-part briefing — overview, key people, recent news,
        financials, and risks — while you finish your coffee.
      </p>
    </div>
  )
}

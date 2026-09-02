import { useEffect, useState } from 'react'
import type { ReportSummary } from '../types'
import { formatRelativeTime } from '../utils/time'

interface ReportHistorySidebarProps {
  reports: ReportSummary[]
  selectedId: number | null
  onSelect: (id: number) => void
  onDelete: (id: number) => void
  loading: boolean
}

export function ReportHistorySidebar({ reports, selectedId, onSelect, onDelete, loading }: ReportHistorySidebarProps) {
  // Force a re-render every 30s so relative timestamps ("3 minutes ago") stay fresh.
  const [, setTick] = useState(0)
  useEffect(() => {
    const id = window.setInterval(() => setTick((t) => t + 1), 30_000)
    return () => window.clearInterval(id)
  }, [])

  return (
    <aside className="flex h-full w-64 shrink-0 flex-col border-r border-slate-200 bg-slate-50/70">
      <div className="border-b border-slate-200 px-4 py-3">
        <h2 className="text-sm font-semibold text-slate-600">Report History</h2>
      </div>
      <div className="flex-1 overflow-y-auto">
        {loading && <p className="px-4 py-4 text-sm text-slate-400">Loading…</p>}
        {!loading && reports.length === 0 && (
          <p className="px-4 py-6 text-sm text-slate-400">No reports yet. Your first search will show up here.</p>
        )}
        <ul>
          {reports.map((report) => (
            <li
              key={report.id}
              className={`group flex items-center gap-1 border-b border-slate-100 px-2 py-1 transition hover:bg-indigo-50 ${
                selectedId === report.id ? 'bg-indigo-50' : ''
              }`}
            >
              <button onClick={() => onSelect(report.id)} className="flex-1 truncate rounded px-2 py-2 text-left">
                <div className="truncate text-sm font-medium text-slate-800">{report.company_name}</div>
                <div className="text-xs text-slate-400">{formatRelativeTime(report.created_at)}</div>
              </button>
              <button
                onClick={() => onDelete(report.id)}
                aria-label={`Delete report for ${report.company_name}`}
                title="Delete report"
                className="shrink-0 rounded p-1.5 text-slate-300 opacity-0 transition hover:bg-red-50 hover:text-red-500 group-hover:opacity-100"
              >
                ✕
              </button>
            </li>
          ))}
        </ul>
      </div>
    </aside>
  )
}

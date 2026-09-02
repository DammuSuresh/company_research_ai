import type {
  FinancialsData,
  KeyPeopleData,
  NewsData,
  OverviewData,
  ReportSections,
  RisksData,
  SectionKey,
  SectionResult,
  SectionStatus,
} from '../types'
import { SECTION_ORDER, SECTION_TITLES } from '../types'
import { formatRelativeTime } from '../utils/time'

interface ReportViewProps {
  companyName: string
  sections: ReportSections
  /** The section currently being worked on, for the live "streaming" indicator. Pass null for a finished/historical report. */
  activeSection: SectionKey | null
  createdAt?: string
}

function StatusBadge({ status, isActive }: { status: SectionStatus | undefined; isActive: boolean }) {
  if (isActive || status === 'searching' || status === 'synthesizing') {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-indigo-100 px-2 py-0.5 text-xs font-medium text-indigo-600">
        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-indigo-500" />
        Live
      </span>
    )
  }
  if (status === 'complete') {
    return <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-700">Done</span>
  }
  if (status === 'unavailable') {
    return <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-500">No data</span>
  }
  if (status === 'error') {
    return <span className="rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-600">Error</span>
  }
  return <span className="rounded-full bg-slate-50 px-2 py-0.5 text-xs font-medium text-slate-400">Waiting</span>
}

function SkeletonLines({ label }: { label: string }) {
  return (
    <div className="space-y-2">
      <p className="text-sm text-indigo-500">{label}</p>
      <div className="h-3 w-full animate-pulse rounded bg-slate-100" />
      <div className="h-3 w-5/6 animate-pulse rounded bg-slate-100" />
    </div>
  )
}

function SectionContent({ section, result }: { section: SectionKey; result: SectionResult | undefined }) {
  const status = result?.status ?? 'pending'

  if (status === 'pending') {
    return <p className="text-sm text-slate-400">Waiting to start…</p>
  }
  if (status === 'searching') {
    return <SkeletonLines label="Searching the web…" />
  }
  if (status === 'synthesizing') {
    return <SkeletonLines label="Analyzing results…" />
  }
  if (status === 'error') {
    return <p className="text-sm text-red-600">Couldn't research this section: {result?.error ?? 'unknown error.'}</p>
  }
  if (status === 'unavailable') {
    return <p className="text-sm text-slate-400 italic">No public data found for this section.</p>
  }

  // status === 'complete'
  switch (section) {
    case 'overview': {
      const data = result?.data as OverviewData
      return <p className="text-sm leading-relaxed text-slate-700">{data.summary}</p>
    }
    case 'key_people': {
      const data = result?.data as KeyPeopleData
      return (
        <ul className="grid gap-2 sm:grid-cols-2">
          {data.people.map((person, i) => (
            <li key={`${person.name}-${i}`} className="rounded-md bg-slate-50 px-3 py-2 text-sm">
              <div className="font-medium text-slate-800">{person.name}</div>
              <div className="text-slate-500">{person.title}</div>
            </li>
          ))}
        </ul>
      )
    }
    case 'news': {
      const data = result?.data as NewsData
      return (
        <ul className="list-disc space-y-1.5 pl-5 text-sm text-slate-700">
          {data.items.map((item, i) => (
            <li key={i}>{item}</li>
          ))}
        </ul>
      )
    }
    case 'financials': {
      const data = result?.data as FinancialsData
      const rows: [string, string | null][] = [
        ['Revenue', data.revenue],
        ['Employees', data.employee_count],
        ['Market Cap', data.market_cap],
        ['YoY Growth', data.yoy_growth],
      ]
      return (
        <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {rows.map(([label, value]) => (
            <div key={label} className="rounded-md bg-slate-50 px-3 py-2">
              <dt className="text-xs tracking-wide text-slate-400 uppercase">{label}</dt>
              <dd className="mt-1 text-sm font-semibold text-slate-800">{value ?? '—'}</dd>
            </div>
          ))}
        </dl>
      )
    }
    case 'risks': {
      const data = result?.data as RisksData
      return (
        <ul className="list-disc space-y-1.5 pl-5 text-sm text-slate-700">
          {data.items.map((item, i) => (
            <li key={i}>{item}</li>
          ))}
        </ul>
      )
    }
  }
}

export function ReportView({ companyName, sections, activeSection, createdAt }: ReportViewProps) {
  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">{companyName}</h1>
        {createdAt && <p className="text-sm text-slate-400">Generated {formatRelativeTime(createdAt)}</p>}
      </div>

      {SECTION_ORDER.map((section) => {
        const result = sections[section]
        const isActive = activeSection === section
        return (
          <section
            key={section}
            className={`rounded-xl border bg-white p-5 shadow-sm transition ${
              isActive ? 'border-indigo-300 ring-2 ring-indigo-100' : 'border-slate-200'
            }`}
          >
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-sm font-semibold tracking-wide text-slate-500 uppercase">{SECTION_TITLES[section]}</h2>
              <StatusBadge status={result?.status} isActive={isActive} />
            </div>
            <SectionContent section={section} result={result} />
          </section>
        )
      })}
    </div>
  )
}

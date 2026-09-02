import { useCallback, useEffect, useState } from 'react'
import { ApiError, deleteReport, getReport, listReports } from './api'
import { EmptyState } from './components/EmptyState'
import { ErrorBanner } from './components/ErrorBanner'
import { ReportHistorySidebar } from './components/ReportHistorySidebar'
import { ReportView } from './components/ReportView'
import { SearchBar } from './components/SearchBar'
import { useResearchStream } from './hooks/useResearchStream'
import { reportDetailToSections } from './types'
import type { ReportSections, ReportSummary } from './types'

type ViewMode = 'live' | 'history'

interface HistoryDetail {
  companyName: string
  createdAt: string
  sections: ReportSections
}

function App() {
  const [reports, setReports] = useState<ReportSummary[]>([])
  const [reportsLoading, setReportsLoading] = useState(true)
  const [reportsError, setReportsError] = useState<string | null>(null)

  const [viewMode, setViewMode] = useState<ViewMode>('live')
  const [selectedHistoryId, setSelectedHistoryId] = useState<number | null>(null)
  const [historyDetail, setHistoryDetail] = useState<HistoryDetail | null>(null)
  const [historyLoading, setHistoryLoading] = useState(false)
  const [historyError, setHistoryError] = useState<string | null>(null)

  const refreshReports = useCallback(async () => {
    try {
      const data = await listReports()
      setReports(data)
      setReportsError(null)
    } catch (err) {
      setReportsError(err instanceof ApiError ? err.message : 'Could not reach the backend. Is it running on port 8000?')
    } finally {
      setReportsLoading(false)
    }
  }, [])

  useEffect(() => {
    refreshReports()
  }, [refreshReports])

  const { state, start, cancel } = useResearchStream(() => {
    refreshReports()
  })

  function handleSearch(companyName: string) {
    setViewMode('live')
    setSelectedHistoryId(null)
    start(companyName)
  }

  async function handleSelectHistory(id: number) {
    setViewMode('history')
    setSelectedHistoryId(id)
    setHistoryLoading(true)
    setHistoryError(null)
    try {
      const report = await getReport(id)
      setHistoryDetail({
        companyName: report.company_name,
        createdAt: report.created_at,
        sections: reportDetailToSections(report),
      })
    } catch (err) {
      setHistoryDetail(null)
      setHistoryError(err instanceof ApiError ? err.message : 'Could not load that report.')
    } finally {
      setHistoryLoading(false)
    }
  }

  async function handleDelete(id: number) {
    try {
      await deleteReport(id)
      if (selectedHistoryId === id) {
        setSelectedHistoryId(null)
        setHistoryDetail(null)
        setViewMode('live')
      }
      await refreshReports()
    } catch (err) {
      setReportsError(err instanceof ApiError ? err.message : 'Could not delete that report.')
    }
  }

  const mockBadgeText = (() => {
    if (!state.mockMode) return null
    const simulated = [state.mockMode.llm && 'LLM', state.mockMode.search && 'search'].filter(Boolean)
    if (simulated.length === 0) return null
    return `Running in demo mode with simulated ${simulated.join(' & ')} data — add API keys in backend/.env for live results.`
  })()

  return (
    <div className="flex h-screen flex-col bg-slate-100">
      <header className="border-b border-slate-200 bg-white px-6 py-4 shadow-sm">
        <h1 className="text-lg font-bold text-slate-900">Company Research Tool</h1>
        <p className="text-sm text-slate-500">Instant sales-meeting briefings, powered by live web search + Gemini.</p>
      </header>

      <div className="flex flex-1 overflow-hidden">
        <ReportHistorySidebar
          reports={reports}
          selectedId={viewMode === 'history' ? selectedHistoryId : null}
          onSelect={handleSelectHistory}
          onDelete={handleDelete}
          loading={reportsLoading}
        />

        <main className="flex-1 overflow-y-auto">
          <div className="mx-auto flex max-w-3xl flex-col gap-4 p-6">
            <SearchBar onSearch={handleSearch} isStreaming={state.phase === 'streaming'} streamingCompany={state.companyName} />

            {viewMode === 'live' && mockBadgeText && state.phase !== 'idle' && (
              <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-2 text-xs text-amber-700">
                {mockBadgeText}
              </div>
            )}

            {reportsError && <ErrorBanner message={reportsError} onDismiss={() => setReportsError(null)} />}

            {viewMode === 'live' && (
              <>
                {state.phase === 'idle' && <EmptyState />}

                {state.phase === 'streaming' && (
                  <>
                    <div className="flex items-center justify-between rounded-lg bg-indigo-50 px-4 py-2 text-sm text-indigo-700">
                      <span>Researching {state.companyName}…</span>
                      <button onClick={cancel} className="font-medium underline hover:text-indigo-900">
                        Cancel
                      </button>
                    </div>
                    <ReportView companyName={state.companyName ?? ''} sections={state.sections} activeSection={state.activeSection} />
                  </>
                )}

                {state.phase === 'complete' && (
                  <ReportView companyName={state.companyName ?? ''} sections={state.sections} activeSection={null} />
                )}

                {state.phase === 'error' && (
                  <>
                    <ErrorBanner message={state.errorMessage ?? 'Something went wrong. Please try again.'} />
                    {Object.keys(state.sections).length > 0 && (
                      <ReportView companyName={state.companyName ?? ''} sections={state.sections} activeSection={null} />
                    )}
                  </>
                )}
              </>
            )}

            {viewMode === 'history' && (
              <>
                {historyLoading && <p className="text-sm text-slate-400">Loading report…</p>}
                {historyError && <ErrorBanner message={historyError} />}
                {historyDetail && !historyLoading && (
                  <ReportView
                    companyName={historyDetail.companyName}
                    sections={historyDetail.sections}
                    activeSection={null}
                    createdAt={historyDetail.createdAt}
                  />
                )}
              </>
            )}
          </div>
        </main>
      </div>
    </div>
  )
}

export default App

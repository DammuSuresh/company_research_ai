import { useCallback, useEffect, useRef, useState } from 'react'
import { ApiError, type ResearchStreamEvent, streamResearch } from '../api'
import type { ReportSections, SectionKey } from '../types'

export type ResearchPhase = 'idle' | 'streaming' | 'complete' | 'error'

export interface ResearchState {
  phase: ResearchPhase
  companyName: string | null
  mockMode: { llm: boolean; search: boolean } | null
  sections: ReportSections
  /** The section currently being searched/synthesized, for the "streaming" visual indicator. */
  activeSection: SectionKey | null
  reportId: number | null
  errorMessage: string | null
}

const INITIAL_STATE: ResearchState = {
  phase: 'idle',
  companyName: null,
  mockMode: null,
  sections: {},
  activeSection: null,
  reportId: null,
  errorMessage: null,
}

function applyEvent(prev: ResearchState, evt: ResearchStreamEvent): ResearchState {
  switch (evt.event) {
    case 'started':
      return { ...prev, mockMode: evt.data.mock_mode }

    case 'section_status':
      return {
        ...prev,
        activeSection: evt.data.section,
        sections: {
          ...prev.sections,
          [evt.data.section]: { status: evt.data.status, data: prev.sections[evt.data.section]?.data ?? null, error: null },
        },
      }

    case 'section_result': {
      const result = {
        status: evt.data.status,
        data: evt.data.data,
        error: evt.data.error,
      } as ReportSections[SectionKey]
      return { ...prev, sections: { ...prev.sections, [evt.data.section]: result } }
    }

    case 'sections_done':
      return prev

    case 'complete':
      return { ...prev, phase: 'complete', activeSection: null, reportId: evt.data.report_id }

    case 'error':
      return { ...prev, phase: 'error', activeSection: null, errorMessage: evt.data.message }

    default:
      return prev
  }
}

/**
 * Drives the POST /api/research SSE stream and exposes a state machine the
 * UI can render directly (idle / streaming / complete / error), including
 * per-section progress. Automatically aborts the in-flight request if the
 * component unmounts or a new search is started.
 */
export function useResearchStream(onComplete?: (reportId: number) => void) {
  const [state, setState] = useState<ResearchState>(INITIAL_STATE)
  const abortRef = useRef<AbortController | null>(null)
  const mountedRef = useRef(true)
  const onCompleteRef = useRef(onComplete)

  useEffect(() => {
    onCompleteRef.current = onComplete
  }, [onComplete])

  useEffect(() => {
    // React 18/19 StrictMode intentionally mounts, cleans up, and remounts
    // every component once in development to surface missing-cleanup bugs.
    // Re-arm the flag here (rather than only setting it false on cleanup)
    // so that dance doesn't leave `mountedRef` permanently false afterwards.
    mountedRef.current = true
    return () => {
      mountedRef.current = false
      abortRef.current?.abort()
    }
  }, [])

  const start = useCallback(async (companyName: string) => {
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller

    setState({ ...INITIAL_STATE, phase: 'streaming', companyName })

    try {
      await streamResearch(companyName, controller.signal, (evt) => {
        if (!mountedRef.current || controller.signal.aborted) return
        setState((prev) => applyEvent(prev, evt))
        if (evt.event === 'complete') {
          onCompleteRef.current?.(evt.data.report_id)
        }
      })
    } catch (err) {
      if (!mountedRef.current || controller.signal.aborted) return
      const message =
        err instanceof ApiError
          ? err.message
          : 'Lost connection to the server while researching. Please check the backend is running and try again.'
      setState((prev) => ({ ...prev, phase: 'error', activeSection: null, errorMessage: message }))
    }
  }, [])

  const cancel = useCallback(() => {
    abortRef.current?.abort()
    setState((prev) => (prev.phase === 'streaming' ? { ...INITIAL_STATE } : prev))
  }, [])

  const reset = useCallback(() => {
    abortRef.current?.abort()
    setState(INITIAL_STATE)
  }, [])

  return { state, start, cancel, reset }
}

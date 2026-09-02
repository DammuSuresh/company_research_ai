// Thin fetch wrapper around the FastAPI backend, plus a small hand-rolled
// SSE parser for the streaming research endpoint.
//
// We don't use the browser's built-in EventSource here because it only
// supports GET requests, and our research endpoint needs a POST body
// (the company name). Instead we POST with fetch and parse the
// `text/event-stream` body ourselves as it arrives.
import type { ReportDetail, ReportSummary, SectionKey, SectionStatus } from './types'

const BASE_URL = '/api'

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function readErrorDetail(res: Response, fallback: string): Promise<string> {
  try {
    const body = await res.json()
    if (typeof body?.detail === 'string') return body.detail
  } catch {
    // response body wasn't JSON -- fall through to the generic message
  }
  return fallback
}

export async function listReports(): Promise<ReportSummary[]> {
  const res = await fetch(`${BASE_URL}/reports`)
  if (!res.ok) {
    throw new ApiError(await readErrorDetail(res, 'Could not load report history.'), res.status)
  }
  return res.json()
}

export async function getReport(id: number): Promise<ReportDetail> {
  const res = await fetch(`${BASE_URL}/reports/${id}`)
  if (!res.ok) {
    throw new ApiError(await readErrorDetail(res, 'Could not load that report.'), res.status)
  }
  return res.json()
}

export async function deleteReport(id: number): Promise<void> {
  const res = await fetch(`${BASE_URL}/reports/${id}`, { method: 'DELETE' })
  if (!res.ok && res.status !== 204) {
    throw new ApiError(await readErrorDetail(res, 'Could not delete that report.'), res.status)
  }
}

export async function checkHealth(): Promise<{ status: string; llm_mock_mode: boolean; search_mock_mode: boolean }> {
  const res = await fetch(`${BASE_URL}/health`)
  if (!res.ok) throw new ApiError('Backend health check failed.', res.status)
  return res.json()
}

// --- Streaming research ---

export interface StartedEventData {
  company_name: string
  mock_mode: { llm: boolean; search: boolean }
}
export interface SectionStatusEventData {
  section: SectionKey
  status: Extract<SectionStatus, 'searching' | 'synthesizing'>
}
export interface SectionResultEventData {
  section: SectionKey
  status: Extract<SectionStatus, 'complete' | 'unavailable' | 'error'>
  data: unknown
  error: string | null
}
export interface CompleteEventData {
  report_id: number
  company_name: string
  created_at: string
}
export interface StreamErrorEventData {
  message: string
}

export type ResearchStreamEvent =
  | { event: 'started'; data: StartedEventData }
  | { event: 'section_status'; data: SectionStatusEventData }
  | { event: 'section_result'; data: SectionResultEventData }
  | { event: 'sections_done'; data: { results: unknown } }
  | { event: 'complete'; data: CompleteEventData }
  | { event: 'error'; data: StreamErrorEventData }

function parseSseBlock(block: string): { event: string; data: unknown } | null {
  let eventType = 'message'
  const dataLines: string[] = []
  for (const line of block.split('\n')) {
    if (line.startsWith('event:')) eventType = line.slice('event:'.length).trim()
    else if (line.startsWith('data:')) dataLines.push(line.slice('data:'.length).trim())
  }
  if (dataLines.length === 0) return null
  try {
    return { event: eventType, data: JSON.parse(dataLines.join('\n')) }
  } catch {
    return null
  }
}

/**
 * POST a company name to /api/research and invoke `onEvent` for each SSE
 * event as it streams in. Resolves once the stream ends; rejects on a
 * non-2xx response or a network failure. Pass `signal` from an
 * AbortController to support cancellation.
 */
export async function streamResearch(
  companyName: string,
  signal: AbortSignal,
  onEvent: (evt: ResearchStreamEvent) => void,
): Promise<void> {
  const res = await fetch(`${BASE_URL}/research`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ company_name: companyName }),
    signal,
  })

  if (!res.ok) {
    throw new ApiError(await readErrorDetail(res, `Research request failed (${res.status}).`), res.status)
  }
  if (!res.body) {
    throw new ApiError('Streaming responses are not supported in this browser.', 0)
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    let sepIndex = buffer.indexOf('\n\n')
    while (sepIndex !== -1) {
      const rawBlock = buffer.slice(0, sepIndex)
      buffer = buffer.slice(sepIndex + 2)
      const parsed = parseSseBlock(rawBlock)
      if (parsed) onEvent(parsed as ResearchStreamEvent)
      sepIndex = buffer.indexOf('\n\n')
    }
  }
}

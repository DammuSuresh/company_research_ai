// Types mirroring the backend's app/schemas.py and app/agent/schemas.py.

export type SectionKey = 'overview' | 'key_people' | 'news' | 'financials' | 'risks'

export const SECTION_ORDER: SectionKey[] = ['overview', 'key_people', 'news', 'financials', 'risks']

export const SECTION_TITLES: Record<SectionKey, string> = {
  overview: 'Company Overview',
  key_people: 'Key People',
  news: 'Recent News',
  financials: 'Financial Highlights',
  risks: 'Risk Factors',
}

export interface KeyPerson {
  name: string
  title: string
}

export interface OverviewData {
  summary: string
}

export interface KeyPeopleData {
  people: KeyPerson[]
}

export interface NewsData {
  items: string[]
}

export interface FinancialsData {
  revenue: string | null
  employee_count: string | null
  market_cap: string | null
  yoy_growth: string | null
}

export interface RisksData {
  items: string[]
}

export type SectionDataMap = {
  overview: OverviewData
  key_people: KeyPeopleData
  news: NewsData
  financials: FinancialsData
  risks: RisksData
}

/** Lifecycle of a single section, from not-yet-started through to a final outcome. */
export type SectionStatus = 'pending' | 'searching' | 'synthesizing' | 'complete' | 'unavailable' | 'error'

export interface SectionResult<K extends SectionKey = SectionKey> {
  status: SectionStatus
  data: SectionDataMap[K] | null
  error?: string | null
}

export type ReportSections = { [K in SectionKey]?: SectionResult<K> }

export interface ReportSummary {
  id: number
  company_name: string
  created_at: string
  status: string
}

export interface ReportDetail extends ReportSummary {
  overview: SectionResult<'overview'> | null
  key_people: SectionResult<'key_people'> | null
  news: SectionResult<'news'> | null
  financials: SectionResult<'financials'> | null
  risks: SectionResult<'risks'> | null
  error_message?: string | null
}

export function reportDetailToSections(report: ReportDetail): ReportSections {
  return {
    overview: report.overview ?? undefined,
    key_people: report.key_people ?? undefined,
    news: report.news ?? undefined,
    financials: report.financials ?? undefined,
    risks: report.risks ?? undefined,
  }
}

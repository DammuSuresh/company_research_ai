/** Backend timestamps are UTC but may be serialized without a trailing
 * offset (SQLite has no native timezone-aware type), e.g.
 * "2026-09-02T07:45:50.571301". Normalize those to explicit UTC before
 * parsing so relative times aren't computed against the wrong offset. */
function parseUtc(iso: string): Date {
  const hasOffset = /Z$|[+-]\d{2}:?\d{2}$/.test(iso)
  return new Date(hasOffset ? iso : `${iso}Z`)
}

export function formatRelativeTime(iso: string, now: Date = new Date()): string {
  const then = parseUtc(iso)
  const seconds = Math.round((now.getTime() - then.getTime()) / 1000)

  if (seconds < 5) return 'just now'
  if (seconds < 60) return `${seconds}s ago`

  const minutes = Math.round(seconds / 60)
  if (minutes < 60) return `${minutes}m ago`

  const hours = Math.round(minutes / 60)
  if (hours < 24) return `${hours}h ago`

  const days = Math.round(hours / 24)
  if (days < 7) return `${days}d ago`

  return then.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })
}

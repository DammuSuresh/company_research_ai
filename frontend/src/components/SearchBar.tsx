import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'

interface SearchBarProps {
  onSearch: (companyName: string) => void
  isStreaming: boolean
  streamingCompany: string | null
}

/** The primary search input. Prominently placed at the top of the app,
 * supports Cmd/Ctrl+K to focus from anywhere, and guards against
 * re-submitting the same company that's already being researched. */
export function SearchBar({ onSearch, isStreaming, streamingCompany }: SearchBarProps) {
  const [value, setValue] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault()
        inputRef.current?.focus()
        inputRef.current?.select()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  const trimmed = value.trim()
  const isDuplicate =
    isStreaming && streamingCompany !== null && trimmed.length > 0 && trimmed.toLowerCase() === streamingCompany.toLowerCase()
  const canSubmit = trimmed.length > 0 && !isDuplicate

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (!canSubmit) return
    onSearch(trimmed)
    setValue('')
  }

  return (
    <div>
      <form onSubmit={handleSubmit} className="flex w-full gap-2">
        <div className="relative flex-1">
          <input
            ref={inputRef}
            type="text"
            value={value}
            onChange={(event) => setValue(event.target.value)}
            placeholder="Enter a company name, e.g. Salesforce…"
            className="w-full rounded-lg border border-slate-300 bg-white px-4 py-3 text-base text-slate-900 shadow-sm placeholder:text-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200"
            aria-label="Company name"
          />
          <kbd className="pointer-events-none absolute top-1/2 right-3 hidden -translate-y-1/2 rounded border border-slate-200 bg-slate-50 px-1.5 py-0.5 text-xs text-slate-400 sm:inline-block">
            ⌘K
          </kbd>
        </div>
        <button
          type="submit"
          disabled={!canSubmit}
          className="rounded-lg bg-indigo-600 px-5 py-3 font-medium text-white shadow-sm transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-slate-300"
        >
          {isStreaming ? 'Researching…' : 'Research'}
        </button>
      </form>
      {isDuplicate && (
        <p className="mt-1.5 text-xs text-slate-500">Already researching "{streamingCompany}" — hang tight.</p>
      )}
    </div>
  )
}

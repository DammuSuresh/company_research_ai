interface ErrorBannerProps {
  message: string
  onDismiss?: () => void
}

/** Human-readable error display — never a raw stack trace. */
export function ErrorBanner({ message, onDismiss }: ErrorBannerProps) {
  return (
    <div role="alert" className="flex items-start justify-between gap-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
      <span>{message}</span>
      {onDismiss && (
        <button onClick={onDismiss} className="shrink-0 font-medium text-red-600 hover:text-red-800">
          Dismiss
        </button>
      )}
    </div>
  )
}

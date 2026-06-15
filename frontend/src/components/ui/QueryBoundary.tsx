import { type ReactNode } from 'react'
import { Loader2, AlertCircle, Inbox } from 'lucide-react'

interface QueryBoundaryProps {
  isLoading: boolean
  isError: boolean
  isEmpty?: boolean
  emptyMessage?: string
  errorMessage?: string
  children: ReactNode
}

/** Standardized loading / error / empty wrapper for data-backed views. */
export function QueryBoundary({
  isLoading,
  isError,
  isEmpty = false,
  emptyMessage = 'Nothing here yet.',
  errorMessage = 'Failed to load data.',
  children,
}: QueryBoundaryProps) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16 text-gray-500">
        <Loader2 className="w-5 h-5 animate-spin mr-2" />
        Loading…
      </div>
    )
  }
  if (isError) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-red-400">
        <AlertCircle className="w-6 h-6 mb-2" />
        <p className="text-sm">{errorMessage}</p>
        <p className="text-xs text-gray-500 mt-1">Is the backend running and Ollama available?</p>
      </div>
    )
  }
  if (isEmpty) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-gray-500">
        <Inbox className="w-6 h-6 mb-2" />
        <p className="text-sm">{emptyMessage}</p>
      </div>
    )
  }
  return <>{children}</>
}

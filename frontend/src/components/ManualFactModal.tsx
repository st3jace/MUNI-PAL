import { useState } from 'react'
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query'
import { X, AlertCircle, Check, Loader2, Info, HelpCircle, BookOpen } from 'lucide-react'
import { api } from '../services/api'
import type { MissingPathInfo, CriticalityTier } from '../types'

interface ManualFactModalProps {
  projectId: string
  pathInfo: MissingPathInfo
  onClose: () => void
  onSuccess?: () => void
}

const criticalityColors: Record<CriticalityTier, { bg: string; text: string }> = {
  critical: { bg: 'bg-red-100', text: 'text-red-700' },
  material: { bg: 'bg-yellow-100', text: 'text-yellow-700' },
  secondary: { bg: 'bg-gray-100', text: 'text-gray-700' },
}

export default function ManualFactModal({
  projectId,
  pathInfo,
  onClose,
  onSuccess,
}: ManualFactModalProps) {
  const [value, setValue] = useState('')
  const [unit, setUnit] = useState('')
  const [note, setNote] = useState('')
  const [autoApprove, setAutoApprove] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showGuidance, setShowGuidance] = useState(true)

  const queryClient = useQueryClient()

  // Fetch schema path metadata for guidance
  const { data: metadata, isLoading: metadataLoading } = useQuery({
    queryKey: ['schema-path-metadata', pathInfo.schema_path],
    queryFn: () => api.getSchemaPathMetadata(pathInfo.schema_path),
    staleTime: 1000 * 60 * 10, // Cache for 10 minutes
  })

  const mutation = useMutation({
    mutationFn: () =>
      api.createManualFact(
        {
          project_id: projectId,
          schema_path: pathInfo.schema_path,
          value: parseValue(value, pathInfo.value_type),
          value_type: pathInfo.value_type,
          unit: unit || undefined,
          note: note || undefined,
        },
        undefined,
        autoApprove
      ),
    onSuccess: () => {
      // Invalidate queries to refresh data
      queryClient.invalidateQueries({ queryKey: ['checklist-summary', projectId] })
      queryClient.invalidateQueries({ queryKey: ['checklist-items', projectId] })
      queryClient.invalidateQueries({ queryKey: ['missing-paths', projectId] })
      queryClient.invalidateQueries({ queryKey: ['facts', projectId] })
      queryClient.invalidateQueries({ queryKey: ['readiness', projectId] })
      onSuccess?.()
      onClose()
    },
    onError: (err: Error) => {
      setError(err.message || 'Failed to create fact')
    },
  })

  const parseValue = (val: string, valueType: string): unknown => {
    switch (valueType) {
      case 'number':
      case 'currency':
      case 'percentage':
        return parseFloat(val) || 0
      case 'boolean':
        return val.toLowerCase() === 'true' || val === '1' || val.toLowerCase() === 'yes'
      case 'date':
        return val // Keep as string, backend handles date parsing
      default:
        return val
    }
  }

  const getInputType = (valueType: string): string => {
    switch (valueType) {
      case 'number':
      case 'currency':
      case 'percentage':
        return 'number'
      case 'date':
        return 'date'
      default:
        return 'text'
    }
  }

  const getPlaceholder = (valueType: string): string => {
    switch (valueType) {
      case 'currency':
        return 'e.g., 50000000'
      case 'percentage':
        return 'e.g., 6.35'
      case 'number':
        return 'Enter a number'
      case 'date':
        return 'Select a date'
      case 'boolean':
        return 'true or false'
      default:
        return 'Enter value'
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!value.trim()) {
      setError('Value is required')
      return
    }

    mutation.mutate()
  }

  const colors = criticalityColors[pathInfo.criticality]

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-full items-center justify-center p-4">
        {/* Backdrop */}
        <div
          className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
          onClick={onClose}
        />

        {/* Modal */}
        <div className="relative w-full max-w-lg transform overflow-hidden rounded-lg bg-white shadow-xl transition-all">
          {/* Header */}
          <div className="border-b border-gray-200 px-6 py-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium text-gray-900">Add Manual Fact</h3>
              <button
                onClick={onClose}
                className="rounded-md p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-500"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
          </div>

          {/* Body */}
          <form onSubmit={handleSubmit} className="px-6 py-4 space-y-4">
            {/* Path info */}
            <div className="rounded-md bg-gray-50 p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-0.5 rounded text-xs font-medium ${colors.bg} ${colors.text}`}>
                    {pathInfo.criticality}
                  </span>
                  <span className="text-sm text-gray-500">{pathInfo.phase}</span>
                </div>
                <button
                  type="button"
                  onClick={() => setShowGuidance(!showGuidance)}
                  className="text-sm text-primary-600 hover:text-primary-700 flex items-center gap-1"
                >
                  <HelpCircle className="h-4 w-4" />
                  {showGuidance ? 'Hide' : 'Show'} Guidance
                </button>
              </div>
              <p className="font-medium text-gray-900">{pathInfo.display_name}</p>
              <p className="text-sm text-gray-500 font-mono mt-1">{pathInfo.schema_path}</p>
              <p className="text-xs text-gray-400 mt-2">
                Required for: {pathInfo.item_code} - {pathInfo.item_title}
              </p>
            </div>

            {/* Guidance Panel */}
            {showGuidance && metadata && (
              <div className="rounded-md border border-blue-200 bg-blue-50 p-4 space-y-3">
                <div className="flex items-start gap-2">
                  <Info className="h-5 w-5 text-blue-500 flex-shrink-0 mt-0.5" />
                  <div>
                    <h4 className="font-medium text-blue-900">What is this?</h4>
                    <p className="text-sm text-blue-800 mt-1">{metadata.description}</p>
                  </div>
                </div>

                <div className="flex items-start gap-2">
                  <BookOpen className="h-5 w-5 text-blue-500 flex-shrink-0 mt-0.5" />
                  <div>
                    <h4 className="font-medium text-blue-900">How to fill this</h4>
                    <p className="text-sm text-blue-800 mt-1">{metadata.guidance}</p>
                  </div>
                </div>

                {metadata.example && (
                  <div className="bg-white rounded p-3 border border-blue-200">
                    <span className="text-xs font-medium text-blue-700 uppercase tracking-wide">Example</span>
                    <p className="text-sm text-gray-900 mt-1 font-mono">
                      {typeof metadata.example === 'object'
                        ? JSON.stringify(metadata.example, null, 2)
                        : String(metadata.example)}
                    </p>
                  </div>
                )}

                {metadata.who_needs_it && metadata.who_needs_it.length > 0 && (
                  <div>
                    <span className="text-xs font-medium text-blue-700">Who needs this:</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {metadata.who_needs_it.map((who) => (
                        <span key={who} className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded">
                          {who}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {metadata.allowed_values && metadata.allowed_values.length > 0 && (
                  <div>
                    <span className="text-xs font-medium text-blue-700">Allowed values:</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {metadata.allowed_values.map((val) => (
                        <span key={val} className="text-xs bg-white text-blue-800 px-2 py-0.5 rounded border border-blue-200">
                          {val}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {metadataLoading && showGuidance && (
              <div className="rounded-md border border-blue-200 bg-blue-50 p-4 text-center">
                <Loader2 className="h-5 w-5 animate-spin mx-auto text-blue-500" />
                <p className="text-sm text-blue-700 mt-1">Loading guidance...</p>
              </div>
            )}

            {/* Value input */}
            <div>
              <label htmlFor="value" className="block text-sm font-medium text-gray-700">
                Value <span className="text-red-500">*</span>
              </label>
              <input
                type={getInputType(pathInfo.value_type)}
                id="value"
                value={value}
                onChange={(e) => setValue(e.target.value)}
                placeholder={getPlaceholder(pathInfo.value_type)}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                step={pathInfo.value_type === 'percentage' ? '0.01' : 'any'}
              />
              <p className="mt-1 text-xs text-gray-500">
                Expected type: {pathInfo.value_type}
              </p>
            </div>

            {/* Unit input (optional) */}
            {(pathInfo.value_type === 'currency' ||
              pathInfo.value_type === 'number' ||
              pathInfo.value_type === 'percentage') && (
              <div>
                <label htmlFor="unit" className="block text-sm font-medium text-gray-700">
                  Unit (optional)
                </label>
                <input
                  type="text"
                  id="unit"
                  value={unit}
                  onChange={(e) => setUnit(e.target.value)}
                  placeholder={
                    pathInfo.value_type === 'currency'
                      ? 'e.g., USD'
                      : pathInfo.value_type === 'percentage'
                      ? 'e.g., %'
                      : 'e.g., MW, tpd'
                  }
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                />
              </div>
            )}

            {/* Note input */}
            <div>
              <label htmlFor="note" className="block text-sm font-medium text-gray-700">
                Note (optional)
              </label>
              <textarea
                id="note"
                rows={2}
                value={note}
                onChange={(e) => setNote(e.target.value)}
                placeholder="Source or context for this value..."
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
              />
            </div>

            {/* Auto-approve checkbox */}
            <div className="flex items-center">
              <input
                type="checkbox"
                id="autoApprove"
                checked={autoApprove}
                onChange={(e) => setAutoApprove(e.target.checked)}
                className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />
              <label htmlFor="autoApprove" className="ml-2 text-sm text-gray-700">
                Auto-approve this fact (skip review)
              </label>
            </div>

            {/* Error message */}
            {error && (
              <div className="rounded-md bg-red-50 p-3">
                <div className="flex">
                  <AlertCircle className="h-5 w-5 text-red-400" />
                  <p className="ml-2 text-sm text-red-700">{error}</p>
                </div>
              </div>
            )}
          </form>

          {/* Footer */}
          <div className="border-t border-gray-200 px-6 py-4 flex justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              onClick={handleSubmit}
              disabled={mutation.isPending}
              className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-primary-600 border border-transparent rounded-md hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {mutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Check className="h-4 w-4 mr-2" />
                  Add Fact
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

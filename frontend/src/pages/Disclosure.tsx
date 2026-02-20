import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  FileText,
  RefreshCw,
  Download,
  CheckCircle,
  AlertTriangle,
  AlertCircle,
  Clock,
  ChevronDown,
  ChevronRight,
} from 'lucide-react'
import { api } from '../services/api'
import type { DisclosureSection, TBDSeverity } from '../types'

const severityColors: Record<TBDSeverity, string> = {
  low: 'bg-gray-100 text-gray-800',
  medium: 'bg-yellow-100 text-yellow-800',
  high: 'bg-orange-100 text-orange-800',
  critical: 'bg-red-100 text-red-800',
}

export default function Disclosure() {
  const { projectId } = useParams<{ projectId: string }>()
  const queryClient = useQueryClient()
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set())
  const [generateError, setGenerateError] = useState<string | null>(null)

  const { data: disclosure, isLoading } = useQuery({
    queryKey: ['disclosure-latest', projectId],
    queryFn: () => api.getLatestDisclosure(projectId!),
    enabled: !!projectId,
  })

  const { data: documents } = useQuery({
    queryKey: ['disclosure-documents', projectId],
    queryFn: () => api.listDisclosureDocuments(projectId!),
    enabled: !!projectId,
  })

  const generateMutation = useMutation({
    mutationFn: () => api.generateDisclosure({ project_id: projectId!, force_regenerate: true }),
    onSuccess: () => {
      setGenerateError(null)
      queryClient.invalidateQueries({ queryKey: ['disclosure-latest', projectId] })
      queryClient.invalidateQueries({ queryKey: ['disclosure-documents', projectId] })
    },
    onError: (error: unknown) => {
      console.error('Disclosure generation failed:', error)
      // Extract error message from Axios error response
      let errorMessage = 'Failed to generate disclosure document'
      if (error && typeof error === 'object') {
        const axiosError = error as { response?: { data?: { detail?: string } }; message?: string }
        if (axiosError.response?.data?.detail) {
          errorMessage = axiosError.response.data.detail
        } else if (axiosError.message) {
          errorMessage = axiosError.message
        }
      }
      setGenerateError(errorMessage)
    },
  })

  const toggleSection = (sectionId: string) => {
    setExpandedSections((prev) => {
      const newSet = new Set(prev)
      if (newSet.has(sectionId)) {
        newSet.delete(sectionId)
      } else {
        newSet.add(sectionId)
      }
      return newSet
    })
  }

  const renderSection = (section: DisclosureSection, level: number = 0) => {
    const isExpanded = expandedSections.has(section.id)
    const hasContent = section.content_md && section.content_md.length > 0

    // Calculate completion percentage based on facts ratio, not confidence
    const completionPercent = section.required_fact_count > 0
      ? (section.present_fact_count / section.required_fact_count) * 100
      : 100
    const completionColor =
      completionPercent >= 80
        ? 'text-green-600'
        : completionPercent >= 50
        ? 'text-yellow-600'
        : 'text-red-600'

    return (
      <div key={section.id} className={`${level > 0 ? 'ml-4 border-l-2 border-gray-200 pl-4' : ''}`}>
        <div
          className="flex items-center justify-between py-3 cursor-pointer hover:bg-gray-50 px-3 rounded"
          onClick={() => toggleSection(section.id)}
        >
          <div className="flex items-center gap-2">
            {hasContent ? (
              isExpanded ? (
                <ChevronDown className="h-4 w-4 text-gray-500" />
              ) : (
                <ChevronRight className="h-4 w-4 text-gray-500" />
              )
            ) : (
              <div className="w-4" />
            )}
            <span className="font-medium text-gray-900">{section.title}</span>
            {section.tbd_count > 0 && (
              <span className="badge badge-warning text-xs">
                {section.tbd_count} TBD
              </span>
            )}
          </div>
          <div className="flex items-center gap-4 text-sm">
            <span className="text-gray-500">
              {section.present_fact_count}/{section.required_fact_count} facts
            </span>
            <span className={`font-medium ${completionColor}`}>
              {completionPercent.toFixed(0)}%
            </span>
          </div>
        </div>
        {isExpanded && hasContent && (
          <div className="px-3 pb-4">
            <div className="prose prose-sm max-w-none bg-gray-50 p-4 rounded-lg">
              <pre className="whitespace-pre-wrap text-sm text-gray-700 font-sans">
                {section.content_md}
              </pre>
            </div>
            {section.tbd_markers && section.tbd_markers.length > 0 && (
              <div className="mt-3 space-y-2">
                <p className="text-sm font-medium text-gray-700">Missing Information:</p>
                {section.tbd_markers.map((tbd) => (
                  <div
                    key={tbd.id}
                    className={`p-2 rounded text-sm ${severityColors[tbd.severity]}`}
                  >
                    <span className="font-medium">{tbd.reason}</span>
                    <div className="mt-1 text-xs opacity-80">
                      Paths: {tbd.missing_fact_paths.join(', ')}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
        {section.subsections?.map((sub) => renderSection(sub, level + 1))}
      </div>
    )
  }

  if (isLoading) {
    return <div className="text-center py-12 text-gray-500">Loading disclosure...</div>
  }

  const completenessPercent = (disclosure?.completeness_score ?? 0) * 100
  const completenessColor =
    completenessPercent >= 80
      ? 'text-green-600'
      : completenessPercent >= 60
      ? 'text-yellow-600'
      : 'text-red-600'

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Disclosure Document</h1>
          <p className="mt-1 text-sm text-gray-500">
            WP7 - Synthesized disclosure from extracted facts
          </p>
        </div>
        <div className="flex items-center gap-3">
          {disclosure && (
            <button
              type="button"
              className="btn btn-secondary flex items-center gap-2"
              onClick={async () => {
                try {
                  const result = await api.exportDisclosure(disclosure.id, 'md')
                  if (result.content) {
                    const blob = new Blob([result.content], { type: 'text/markdown' })
                    const url = URL.createObjectURL(blob)
                    const a = document.createElement('a')
                    a.href = url
                    a.download = result.filename || `disclosure_v${disclosure.version}.md`
                    document.body.appendChild(a)
                    a.click()
                    document.body.removeChild(a)
                    URL.revokeObjectURL(url)
                  }
                } catch (error) {
                  console.error('Export failed:', error)
                  setGenerateError('Failed to export disclosure document')
                }
              }}
            >
              <Download className="h-4 w-4" />
              Export
            </button>
          )}
          <button
            type="button"
            className="btn btn-primary flex items-center gap-2"
            onClick={() => generateMutation.mutate()}
            disabled={generateMutation.isPending}
          >
            <RefreshCw className={`h-4 w-4 ${generateMutation.isPending ? 'animate-spin' : ''}`} />
            {disclosure ? 'Regenerate' : 'Generate'}
          </button>
        </div>
      </div>

      {/* Error Display */}
      {generateError && (
        <div className="card p-4 border-red-200 bg-red-50">
          <div className="flex items-center gap-3">
            <AlertCircle className="h-5 w-5 text-red-500 flex-shrink-0" />
            <div>
              <p className="font-medium text-red-800">Generation Failed</p>
              <p className="text-sm text-red-600">{generateError}</p>
            </div>
            <button
              onClick={() => setGenerateError(null)}
              className="ml-auto text-red-400 hover:text-red-600"
            >
              &times;
            </button>
          </div>
        </div>
      )}

      {/* Status Overview */}
      {disclosure ? (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="card p-5">
              <div className="flex items-center gap-3">
                <FileText className="h-8 w-8 text-blue-500" />
                <div>
                  <p className="text-2xl font-bold">v{disclosure.version}</p>
                  <p className="text-sm text-gray-500">Version</p>
                </div>
              </div>
            </div>
            <div className="card p-5">
              <div className="flex items-center gap-3">
                <CheckCircle className={`h-8 w-8 ${completenessColor}`} />
                <div>
                  <p className={`text-2xl font-bold ${completenessColor}`}>
                    {completenessPercent.toFixed(0)}%
                  </p>
                  <p className="text-sm text-gray-500">Completeness</p>
                </div>
              </div>
            </div>
            <div className="card p-5">
              <div className="flex items-center gap-3">
                <AlertTriangle className="h-8 w-8 text-yellow-500" />
                <div>
                  <p className="text-2xl font-bold">{disclosure.tbd_items?.length ?? 0}</p>
                  <p className="text-sm text-gray-500">TBD Items</p>
                </div>
              </div>
            </div>
            <div className="card p-5">
              <div className="flex items-center gap-3">
                <Clock className="h-8 w-8 text-gray-500" />
                <div>
                  <p className="text-2xl font-bold">{disclosure.sections?.length ?? 0}</p>
                  <p className="text-sm text-gray-500">Sections</p>
                </div>
              </div>
            </div>
          </div>

          {/* Sections */}
          <div className="card">
            <div className="border-b border-gray-200 px-5 py-4">
              <h2 className="text-lg font-medium text-gray-900">Document Sections</h2>
              <p className="text-sm text-gray-500">
                Expand sections to view synthesized content
              </p>
            </div>
            <div className="divide-y divide-gray-200">
              {disclosure.sections?.map((section) => renderSection(section))}
            </div>
          </div>

          {/* TBD Summary */}
          {disclosure.tbd_items && disclosure.tbd_items.length > 0 && (
            <div className="card">
              <div className="border-b border-gray-200 px-5 py-4 bg-yellow-50">
                <h2 className="text-lg font-medium text-yellow-800">
                  Missing Information ({disclosure.tbd_items.length} items)
                </h2>
                <p className="text-sm text-yellow-600">
                  These items need to be addressed to complete the disclosure
                </p>
              </div>
              <ul className="divide-y divide-gray-200">
                {disclosure.tbd_items.map((tbd) => (
                  <li key={tbd.id} className="px-5 py-4">
                    <div className="flex items-start justify-between">
                      <div>
                        <span className={`badge ${severityColors[tbd.severity]}`}>
                          {tbd.severity.toUpperCase()}
                        </span>
                        <p className="mt-2 font-medium text-gray-900">{tbd.reason}</p>
                        <p className="mt-1 text-sm text-gray-500">
                          Location: {tbd.location}
                        </p>
                      </div>
                      {tbd.is_resolved && (
                        <CheckCircle className="h-5 w-5 text-green-500" />
                      )}
                    </div>
                    <div className="mt-2 flex flex-wrap gap-1">
                      {tbd.missing_fact_paths.map((path) => (
                        <code
                          key={path}
                          className="text-xs bg-gray-100 px-2 py-1 rounded"
                        >
                          {path}
                        </code>
                      ))}
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Version History */}
          {documents && documents.documents.length > 1 && (
            <div className="card">
              <div className="border-b border-gray-200 px-5 py-4">
                <h2 className="text-lg font-medium text-gray-900">Version History</h2>
              </div>
              <ul className="divide-y divide-gray-200">
                {documents.documents.map((doc) => (
                  <li key={doc.id} className="px-5 py-4 flex items-center justify-between">
                    <div>
                      <span className="font-medium">Version {doc.version}</span>
                      <span className="ml-2 text-sm text-gray-500">
                        {new Date(doc.created_at).toLocaleString()}
                      </span>
                    </div>
                    <div className="flex items-center gap-4">
                      <span className="text-sm">
                        {(doc.completeness_score * 100).toFixed(0)}% complete
                      </span>
                      <span className="text-sm text-gray-500">
                        {doc.tbd_count} TBDs
                      </span>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </>
      ) : (
        <div className="card p-12 text-center">
          <FileText className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-4 text-lg font-medium text-gray-900">
            No Disclosure Document Yet
          </h3>
          <p className="mt-2 text-sm text-gray-500">
            Generate a disclosure document to synthesize your extracted facts into
            disclosure-ready prose.
          </p>
          <button
            type="button"
            className="mt-6 btn btn-primary"
            onClick={() => generateMutation.mutate()}
            disabled={generateMutation.isPending}
          >
            Generate Disclosure Document
          </button>
        </div>
      )}
    </div>
  )
}

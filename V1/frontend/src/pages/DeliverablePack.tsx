import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  FileText,
  Download,
  RefreshCw,
  Plus,
  ChevronDown,
  ChevronRight,
  AlertCircle,
  CheckCircle,
  Clock,
  Loader2,
} from 'lucide-react'
import { api } from '../services/api'
import type { DeliverablePack, DeliverableSection } from '../types'

const sectionDescriptions: Record<number, string> = {
  1: 'Project metadata, date, readiness summary, and disclaimers',
  2: 'Templated narrative with parties, technology, capital structure, and financials',
  3: 'Dimension scores, critical/material gaps, and priority actions',
  4: 'Phase-by-phase completion percentages and item counts',
  5: 'Complete index of all approved facts with schema paths, values, and confidence',
  6: 'Low-confidence facts requiring verification and validation gaps',
  7: 'Capital structure, CAB mechanics, revenue/OPEX, and DSCR tables',
  8: 'Sustainability-linked bond KPIs and baselines (if enabled)',
  9: 'Skeleton outline for Official Statement preparation',
}

export default function DeliverablePackPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const queryClient = useQueryClient()
  const [expandedSections, setExpandedSections] = useState<Set<number>>(new Set([1]))
  const [selectedPackId, setSelectedPackId] = useState<string | null>(null)

  // Fetch list of existing packs
  const { data: packsData, isLoading: loadingPacks } = useQuery({
    queryKey: ['deliverable-packs', projectId],
    queryFn: () => api.listDeliverablePacks(projectId!),
    enabled: !!projectId,
  })

  // Fetch selected pack details
  const { data: selectedPack, isLoading: loadingPack } = useQuery({
    queryKey: ['deliverable-pack', selectedPackId],
    queryFn: () => api.getDeliverablePack(selectedPackId!),
    enabled: !!selectedPackId,
    refetchInterval: (query) => {
      // Poll while pack is generating
      if (query.state.data && !query.state.data.is_complete) {
        return 2000
      }
      return false
    },
  })

  // Create new pack mutation
  const createMutation = useMutation({
    mutationFn: () =>
      api.createDeliverablePack({
        project_id: projectId!,
        title: `Advisor Handoff Pack - ${new Date().toLocaleDateString()}`,
        generated_for: 'Municipal Advisor Review',
      }),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['deliverable-packs', projectId] })
      setSelectedPackId(data.pack_id)
    },
  })

  // Regenerate pack mutation
  const regenerateMutation = useMutation({
    mutationFn: (packId: string) => api.regenerateDeliverablePack(packId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['deliverable-pack', selectedPackId] })
    },
  })

  const toggleSection = (sectionNumber: number) => {
    const newExpanded = new Set(expandedSections)
    if (newExpanded.has(sectionNumber)) {
      newExpanded.delete(sectionNumber)
    } else {
      newExpanded.add(sectionNumber)
    }
    setExpandedSections(newExpanded)
  }

  const expandAll = () => {
    setExpandedSections(new Set([1, 2, 3, 4, 5, 6, 7, 8, 9]))
  }

  const collapseAll = () => {
    setExpandedSections(new Set())
  }

  const handleExportMarkdown = async () => {
    if (!selectedPackId) return
    try {
      const markdown = await api.exportDeliverableMarkdown(selectedPackId)
      const blob = new Blob([markdown], { type: 'text/markdown' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `handoff-pack-${selectedPackId.slice(0, 8)}.md`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Export failed:', error)
    }
  }

  if (loadingPacks) {
    return <div className="text-center py-12 text-gray-500">Loading deliverable packs...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">BFMS Hand-Off Pack</h1>
          <p className="mt-1 text-sm text-gray-500">
            Generate advisor-ready deliverable documentation for municipal bond counsel
          </p>
        </div>
        <button
          onClick={() => createMutation.mutate()}
          disabled={createMutation.isPending}
          className="btn btn-primary inline-flex items-center gap-2"
        >
          {createMutation.isPending ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Plus className="h-4 w-4" />
          )}
          Generate New Pack
        </button>
      </div>

      {/* Pack Selection */}
      {packsData && packsData.packs.length > 0 && (
        <div className="card p-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select Pack
          </label>
          <div className="flex gap-4 flex-wrap">
            {packsData.packs.map((pack) => (
              <button
                key={pack.id}
                onClick={() => setSelectedPackId(pack.id)}
                className={`p-3 rounded-lg border text-left transition-all ${
                  selectedPackId === pack.id
                    ? 'border-primary-500 bg-primary-50 ring-2 ring-primary-200'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center gap-2">
                  <FileText className="h-4 w-4 text-gray-400" />
                  <span className="font-medium text-gray-900">{pack.title}</span>
                  {pack.is_complete ? (
                    <CheckCircle className="h-4 w-4 text-green-500" />
                  ) : (
                    <Clock className="h-4 w-4 text-yellow-500 animate-pulse" />
                  )}
                </div>
                <div className="mt-1 text-xs text-gray-500">
                  {new Date(pack.created_at).toLocaleString()}
                  {pack.readiness_score_at_generation !== null && (
                    <span className="ml-2">
                      Score: {pack.readiness_score_at_generation?.toFixed(1)}/10
                    </span>
                  )}
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Selected Pack Content */}
      {selectedPackId && (
        <>
          {loadingPack ? (
            <div className="text-center py-12 text-gray-500">
              <Loader2 className="h-8 w-8 animate-spin mx-auto mb-2" />
              Loading pack...
            </div>
          ) : selectedPack ? (
            <>
              {/* Pack Header */}
              <div className="card p-6">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h2 className="text-xl font-bold text-gray-900">{selectedPack.title}</h2>
                    <p className="text-sm text-gray-500">
                      Generated for: {selectedPack.generated_for}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    {selectedPack.is_complete ? (
                      <>
                        <button
                          onClick={() => regenerateMutation.mutate(selectedPackId)}
                          disabled={regenerateMutation.isPending}
                          className="btn btn-secondary inline-flex items-center gap-2"
                        >
                          {regenerateMutation.isPending ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <RefreshCw className="h-4 w-4" />
                          )}
                          Regenerate
                        </button>
                        <button
                          onClick={handleExportMarkdown}
                          className="btn btn-primary inline-flex items-center gap-2"
                        >
                          <Download className="h-4 w-4" />
                          Export Markdown
                        </button>
                      </>
                    ) : (
                      <span className="inline-flex items-center gap-2 text-yellow-600">
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Generating...
                      </span>
                    )}
                  </div>
                </div>

                {/* Pack Stats */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-4">
                  <div className="bg-gray-50 rounded-lg p-3">
                    <p className="text-2xl font-bold text-gray-900">
                      {selectedPack.readiness_score_at_generation?.toFixed(1) ?? '—'}
                    </p>
                    <p className="text-xs text-gray-500">Readiness Score</p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-3">
                    <p className="text-2xl font-bold text-gray-900">
                      {selectedPack.facts_included_count}
                    </p>
                    <p className="text-xs text-gray-500">Facts Included</p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-3">
                    <p className="text-2xl font-bold text-gray-900">
                      {selectedPack.sections.length}
                    </p>
                    <p className="text-xs text-gray-500">Sections Generated</p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-3">
                    <p className="text-2xl font-bold text-gray-900">
                      {selectedPack.warnings.length}
                    </p>
                    <p className="text-xs text-gray-500">Warnings</p>
                  </div>
                </div>

                {/* Pack-level Warnings */}
                {selectedPack.warnings.length > 0 && (
                  <div className="mt-4 p-4 bg-yellow-50 rounded-lg border border-yellow-200">
                    <div className="flex items-center gap-2 text-yellow-800 font-medium mb-2">
                      <AlertCircle className="h-4 w-4" />
                      Generation Warnings
                    </div>
                    <ul className="list-disc list-inside text-sm text-yellow-700 space-y-1">
                      {selectedPack.warnings.map((warning, i) => (
                        <li key={i}>{warning}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              {/* Expand/Collapse Controls */}
              <div className="flex items-center gap-4">
                <button onClick={expandAll} className="text-sm text-primary-600 hover:underline">
                  Expand All
                </button>
                <button onClick={collapseAll} className="text-sm text-primary-600 hover:underline">
                  Collapse All
                </button>
              </div>

              {/* Sections */}
              <div className="space-y-4">
                {selectedPack.sections.map((section) => (
                  <SectionCard
                    key={section.section_number}
                    section={section}
                    isExpanded={expandedSections.has(section.section_number)}
                    onToggle={() => toggleSection(section.section_number)}
                    description={sectionDescriptions[section.section_number]}
                  />
                ))}
              </div>

              {/* Disclaimer */}
              <div className="card p-6 bg-gray-50">
                <h3 className="text-sm font-medium text-gray-700 mb-2">Disclaimer</h3>
                <p className="text-xs text-gray-500">{selectedPack.disclaimer}</p>
              </div>
            </>
          ) : (
            <div className="text-center py-12 text-gray-500">
              Pack not found
            </div>
          )}
        </>
      )}

      {/* Empty State */}
      {(!packsData || packsData.packs.length === 0) && !createMutation.isPending && (
        <div className="card p-12 text-center">
          <FileText className="h-12 w-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Hand-Off Packs Yet</h3>
          <p className="text-sm text-gray-500 mb-4 max-w-md mx-auto">
            Generate your first BFMS Hand-Off Pack to create a comprehensive advisor-ready
            deliverable containing all approved facts, readiness assessment, and checklist status.
          </p>
          <button
            onClick={() => createMutation.mutate()}
            className="btn btn-primary inline-flex items-center gap-2"
          >
            <Plus className="h-4 w-4" />
            Generate First Pack
          </button>
        </div>
      )}
    </div>
  )
}

interface SectionCardProps {
  section: DeliverableSection
  isExpanded: boolean
  onToggle: () => void
  description?: string
}

function SectionCard({ section, isExpanded, onToggle, description }: SectionCardProps) {
  return (
    <div className="card overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full px-5 py-4 flex items-center justify-between text-left hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-3">
          {isExpanded ? (
            <ChevronDown className="h-5 w-5 text-gray-400" />
          ) : (
            <ChevronRight className="h-5 w-5 text-gray-400" />
          )}
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-primary-600">
                Section {section.section_number}
              </span>
              <span className="font-medium text-gray-900">{section.section_name}</span>
              {section.is_complete ? (
                <CheckCircle className="h-4 w-4 text-green-500" />
              ) : (
                <AlertCircle className="h-4 w-4 text-yellow-500" />
              )}
            </div>
            {description && (
              <p className="text-xs text-gray-500 mt-0.5">{description}</p>
            )}
          </div>
        </div>
        {section.warnings.length > 0 && (
          <span className="inline-flex items-center gap-1 text-xs text-yellow-600 bg-yellow-50 px-2 py-1 rounded">
            <AlertCircle className="h-3 w-3" />
            {section.warnings.length} warning{section.warnings.length !== 1 ? 's' : ''}
          </span>
        )}
      </button>

      {isExpanded && (
        <div className="border-t border-gray-200">
          {/* Section Warnings */}
          {section.warnings.length > 0 && (
            <div className="px-5 py-3 bg-yellow-50 border-b border-yellow-100">
              <ul className="list-disc list-inside text-sm text-yellow-700 space-y-1">
                {section.warnings.map((warning, i) => (
                  <li key={i}>{warning}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Section Content */}
          <div className="px-5 py-4">
            <div
              className="prose prose-sm max-w-none prose-headings:text-gray-900 prose-p:text-gray-700 prose-code:bg-gray-100 prose-code:px-1 prose-code:rounded"
              dangerouslySetInnerHTML={{ __html: markdownToHtml(section.content) }}
            />
          </div>
        </div>
      )}
    </div>
  )
}

// Simple markdown to HTML converter for display
function markdownToHtml(markdown: string): string {
  return markdown
    // Headers
    .replace(/^### (.*$)/gim, '<h3>$1</h3>')
    .replace(/^## (.*$)/gim, '<h2>$1</h2>')
    .replace(/^# (.*$)/gim, '<h1>$1</h1>')
    // Bold
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    // Italic
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    // Code blocks
    .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
    // Inline code
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    // Unordered lists
    .replace(/^\- (.*$)/gim, '<li>$1</li>')
    // Ordered lists
    .replace(/^\d+\. (.*$)/gim, '<li>$1</li>')
    // Horizontal rules
    .replace(/^---$/gim, '<hr />')
    // Line breaks
    .replace(/\n/g, '<br />')
    // Wrap consecutive <li> in <ul>
    .replace(/(<li>.*<\/li>)(<br \/>)?(<li>)/g, '$1$3')
    .replace(/(<li>.*<\/li>)/g, '<ul>$1</ul>')
    // Clean up nested br in ul
    .replace(/<ul><br \/>/g, '<ul>')
    .replace(/<\/ul><br \/>/g, '</ul>')
}

import { useState, useMemo } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  CheckCircle,
  Circle,
  AlertCircle,
  Clock,
  ChevronRight,
  Plus,
  FileEdit,
  Info,
} from 'lucide-react'
import { api } from '../services/api'
import { ChecklistPhase, ChecklistStatus, CriticalityTier } from '../types'
import type { MissingPathInfo } from '../types'
import ManualFactModal from '../components/ManualFactModal'

const phaseNames: Record<ChecklistPhase, string> = {
  [ChecklistPhase.P1]: 'Issuer Authority & Deal Formation',
  [ChecklistPhase.P2]: 'Project & Technology Definition',
  [ChecklistPhase.P3]: 'Financial Structure & Revenue Model',
  [ChecklistPhase.P4]: 'Risk, Security & Disclosure',
  [ChecklistPhase.P5]: 'SLB Architecture & Final Modeling',
  [ChecklistPhase.P6]: 'Advisor Engagement & Execution',
}

const statusConfig = {
  [ChecklistStatus.NOT_STARTED]: {
    label: 'Not Started',
    icon: Circle,
    color: 'text-gray-400',
    bg: 'bg-gray-100',
  },
  [ChecklistStatus.IN_PROGRESS]: {
    label: 'In Progress',
    icon: Clock,
    color: 'text-yellow-500',
    bg: 'bg-yellow-100',
  },
  [ChecklistStatus.BLOCKED]: {
    label: 'Blocked',
    icon: AlertCircle,
    color: 'text-red-500',
    bg: 'bg-red-100',
  },
  [ChecklistStatus.READY]: {
    label: 'Ready',
    icon: CheckCircle,
    color: 'text-green-500',
    bg: 'bg-green-100',
  },
}

export default function Checklist() {
  const { projectId } = useParams<{ projectId: string }>()
  const [expandedPhase, setExpandedPhase] = useState<ChecklistPhase | null>(
    ChecklistPhase.P1
  )
  const [selectedMissingPath, setSelectedMissingPath] = useState<MissingPathInfo | null>(null)

  const { data: summaryData } = useQuery({
    queryKey: ['checklist-summary', projectId],
    queryFn: () => api.getChecklistSummary(projectId!),
    enabled: !!projectId,
  })

  const { data: itemsData, isLoading: itemsLoading } = useQuery({
    queryKey: ['checklist-items', projectId, expandedPhase],
    queryFn: () =>
      api.listChecklistItems({
        project_id: projectId!,
        phase: expandedPhase!,
      }),
    enabled: !!projectId && !!expandedPhase,
  })

  const { data: missingPaths, isLoading: missingPathsLoading } = useQuery({
    queryKey: ['missing-paths', projectId],
    queryFn: () => api.getMissingPaths(projectId!),
    enabled: !!projectId,
  })

  // Get all unique missing paths to fetch their metadata
  const missingPathsList = useMemo(() => {
    return missingPaths?.map(p => p.schema_path) || []
  }, [missingPaths])

  // Fetch metadata for all missing paths (batch request)
  const { data: pathsMetadata } = useQuery({
    queryKey: ['schema-paths-metadata-batch', missingPathsList],
    queryFn: () => api.getSchemaPathsMetadataBatch(missingPathsList),
    enabled: missingPathsList.length > 0,
    staleTime: 1000 * 60 * 10, // Cache for 10 minutes
  })

  const phases = Object.values(ChecklistPhase)

  // Group missing paths by criticality
  const groupedMissingPaths: Partial<Record<CriticalityTier, MissingPathInfo[]>> = missingPaths?.reduce(
    (acc, path) => {
      const criticality = path.criticality as CriticalityTier
      if (!acc[criticality]) {
        acc[criticality] = []
      }
      acc[criticality].push(path)
      return acc
    },
    {} as Partial<Record<CriticalityTier, MissingPathInfo[]>>
  ) ?? {}

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Checklist</h1>
        <p className="mt-1 text-sm text-gray-500">
          Track diligence progress across P1-P6 phases
        </p>
      </div>

      {/* Phase Progress */}
      <div className="card p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Phase Progress</h2>
        <div className="flex items-center gap-2">
          {phases.map((phase, index) => {
            const summary = summaryData?.[phase]
            const percentage = summary?.completion_percentage ?? 0

            return (
              <div key={phase} className="flex items-center">
                <button
                  onClick={() =>
                    setExpandedPhase(expandedPhase === phase ? null : phase)
                  }
                  className={`relative flex flex-col items-center p-3 rounded-lg transition-colors ${
                    expandedPhase === phase
                      ? 'bg-primary-100 ring-2 ring-primary-500'
                      : 'hover:bg-gray-100'
                  }`}
                >
                  <div
                    className={`w-10 h-10 rounded-full flex items-center justify-center font-medium ${
                      percentage === 100
                        ? 'bg-green-500 text-white'
                        : percentage > 0
                        ? 'bg-yellow-500 text-white'
                        : 'bg-gray-200 text-gray-600'
                    }`}
                  >
                    {phase}
                  </div>
                  <span className="mt-1 text-xs text-gray-500">
                    {percentage.toFixed(0)}%
                  </span>
                </button>
                {index < phases.length - 1 && (
                  <ChevronRight className="h-5 w-5 text-gray-300 mx-1" />
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* Phase Detail */}
      {expandedPhase && (
        <div className="card">
          <div className="border-b border-gray-200 px-5 py-4">
            <h2 className="text-lg font-medium text-gray-900">
              {expandedPhase}: {phaseNames[expandedPhase]}
            </h2>
            {summaryData?.[expandedPhase] && (
              <p className="mt-1 text-sm text-gray-500">
                {summaryData[expandedPhase].ready_count} of{' '}
                {summaryData[expandedPhase].total_items} items ready
              </p>
            )}
          </div>

          {itemsLoading ? (
            <div className="p-8 text-center text-gray-500">Loading items...</div>
          ) : itemsData?.checklist_items.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              No checklist items defined for this phase.
            </div>
          ) : (
            <ul className="divide-y divide-gray-200">
              {itemsData?.checklist_items.map((item) => {
                const config = statusConfig[item.status as ChecklistStatus]
                const StatusIcon = config.icon

                return (
                  <li key={item.item_code} className="px-5 py-4 hover:bg-gray-50">
                    <div className="flex items-start gap-4">
                      <div className={`p-2 rounded-lg ${config.bg}`}>
                        <StatusIcon className={`h-5 w-5 ${config.color}`} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium text-gray-500">
                            {item.item_code}
                          </span>
                          <span className={`badge ${config.bg} ${config.color}`}>
                            {config.label}
                          </span>
                        </div>
                        <p className="mt-1 font-medium text-gray-900">{item.title}</p>
                        <p className="mt-1 text-sm text-gray-500">{item.status_reason}</p>
                        <div className="mt-2 flex items-center gap-4 text-sm text-gray-500">
                          <span>
                            Required paths: {item.covered_paths_count}/
                            {item.required_paths_count} ({item.coverage_percentage.toFixed(0)}%)
                          </span>
                        </div>
                        {item.missing_paths && item.missing_paths.length > 0 && (
                          <div className="mt-2 text-sm text-orange-600">
                            <AlertCircle className="inline h-4 w-4 mr-1" />
                            Missing: {item.missing_paths.slice(0, 3).join(', ')}
                            {item.missing_paths.length > 3 && ` +${item.missing_paths.length - 3} more`}
                          </div>
                        )}
                        {item.low_confidence_paths && item.low_confidence_paths.length > 0 && (
                          <div className="mt-1 text-sm text-yellow-600">
                            <Clock className="inline h-4 w-4 mr-1" />
                            Low confidence: {item.low_confidence_paths.join(', ')}
                          </div>
                        )}
                      </div>
                    </div>
                  </li>
                )
              })}
            </ul>
          )}
        </div>
      )}

      {/* Outstanding Items - Manual Entry */}
      <div className="card">
        <div className="border-b border-gray-200 px-5 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-medium text-gray-900">Outstanding Items</h2>
              <p className="mt-1 text-sm text-gray-500">
                Missing facts that you can manually enter if you have the information
              </p>
            </div>
            <div className="flex items-center gap-2">
              <FileEdit className="h-5 w-5 text-gray-400" />
              <span className="text-sm font-medium text-gray-600">
                {missingPaths?.length || 0} items
              </span>
            </div>
          </div>
        </div>

        {missingPathsLoading ? (
          <div className="p-8 text-center text-gray-500">Loading outstanding items...</div>
        ) : !missingPaths?.length ? (
          <div className="p-8 text-center">
            <CheckCircle className="h-12 w-12 mx-auto text-green-500 mb-3" />
            <p className="text-gray-600 font-medium">All required facts have been entered!</p>
            <p className="text-sm text-gray-500 mt-1">
              No outstanding items remaining.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {/* Critical items first */}
            {(groupedMissingPaths[CriticalityTier.CRITICAL]?.length ?? 0) > 0 && (
              <div className="p-4">
                <div className="flex items-center gap-2 mb-3">
                  <AlertCircle className="h-4 w-4 text-red-500" />
                  <span className="text-sm font-medium text-red-700">
                    Critical ({groupedMissingPaths[CriticalityTier.CRITICAL]?.length ?? 0})
                  </span>
                </div>
                <div className="space-y-2">
                  {groupedMissingPaths[CriticalityTier.CRITICAL]?.map((path) => {
                    const meta = pathsMetadata?.[path.schema_path]
                    return (
                      <div
                        key={path.schema_path}
                        className="flex items-center justify-between p-3 bg-red-50 rounded-lg hover:bg-red-100 transition-colors"
                      >
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-gray-900 truncate">
                            {path.display_name}
                          </p>
                          {meta?.short_description && (
                            <p className="text-xs text-red-700 mt-0.5 flex items-start gap-1">
                              <Info className="h-3 w-3 flex-shrink-0 mt-0.5" />
                              {meta.short_description}
                            </p>
                          )}
                          <p className="text-xs text-gray-500 mt-1">
                            {path.item_code}: {path.item_title}
                          </p>
                        </div>
                        <button
                          onClick={() => setSelectedMissingPath(path)}
                          className="ml-4 inline-flex items-center px-3 py-1.5 text-sm font-medium text-red-700 bg-white border border-red-300 rounded-md hover:bg-red-50"
                        >
                          <Plus className="h-4 w-4 mr-1" />
                          Add
                        </button>
                      </div>
                    )
                  })}
                </div>
              </div>
            )}

            {/* Material items */}
            {(groupedMissingPaths[CriticalityTier.MATERIAL]?.length ?? 0) > 0 && (
              <div className="p-4">
                <div className="flex items-center gap-2 mb-3">
                  <Clock className="h-4 w-4 text-yellow-500" />
                  <span className="text-sm font-medium text-yellow-700">
                    Material ({groupedMissingPaths[CriticalityTier.MATERIAL]?.length ?? 0})
                  </span>
                </div>
                <div className="space-y-2">
                  {groupedMissingPaths[CriticalityTier.MATERIAL]?.map((path) => {
                    const meta = pathsMetadata?.[path.schema_path]
                    return (
                      <div
                        key={path.schema_path}
                        className="flex items-center justify-between p-3 bg-yellow-50 rounded-lg hover:bg-yellow-100 transition-colors"
                      >
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-gray-900 truncate">
                            {path.display_name}
                          </p>
                          {meta?.short_description && (
                            <p className="text-xs text-yellow-700 mt-0.5 flex items-start gap-1">
                              <Info className="h-3 w-3 flex-shrink-0 mt-0.5" />
                              {meta.short_description}
                            </p>
                          )}
                          <p className="text-xs text-gray-500 mt-1">
                            {path.item_code}: {path.item_title}
                          </p>
                        </div>
                        <button
                          onClick={() => setSelectedMissingPath(path)}
                          className="ml-4 inline-flex items-center px-3 py-1.5 text-sm font-medium text-yellow-700 bg-white border border-yellow-300 rounded-md hover:bg-yellow-50"
                        >
                          <Plus className="h-4 w-4 mr-1" />
                          Add
                        </button>
                      </div>
                    )
                  })}
                </div>
              </div>
            )}

            {/* Secondary items (collapsed by default) */}
            {(groupedMissingPaths[CriticalityTier.SECONDARY]?.length ?? 0) > 0 && (
              <div className="p-4">
                <details>
                  <summary className="flex items-center gap-2 cursor-pointer">
                    <Circle className="h-4 w-4 text-gray-400" />
                    <span className="text-sm font-medium text-gray-600">
                      Secondary ({groupedMissingPaths[CriticalityTier.SECONDARY]?.length ?? 0})
                    </span>
                  </summary>
                  <div className="mt-3 space-y-2">
                    {groupedMissingPaths[CriticalityTier.SECONDARY]?.map((path) => {
                      const meta = pathsMetadata?.[path.schema_path]
                      return (
                        <div
                          key={path.schema_path}
                          className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                        >
                          <div className="flex-1 min-w-0">
                            <p className="font-medium text-gray-900 truncate">
                              {path.display_name}
                            </p>
                            {meta?.short_description && (
                              <p className="text-xs text-gray-600 mt-0.5 flex items-start gap-1">
                                <Info className="h-3 w-3 flex-shrink-0 mt-0.5" />
                                {meta.short_description}
                              </p>
                            )}
                            <p className="text-xs text-gray-500 mt-1">
                              {path.item_code}: {path.item_title}
                            </p>
                          </div>
                          <button
                            onClick={() => setSelectedMissingPath(path)}
                            className="ml-4 inline-flex items-center px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                          >
                            <Plus className="h-4 w-4 mr-1" />
                            Add
                          </button>
                        </div>
                      )
                    })}
                  </div>
                </details>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Manual Fact Modal */}
      {selectedMissingPath && projectId && (
        <ManualFactModal
          projectId={projectId}
          pathInfo={selectedMissingPath}
          onClose={() => setSelectedMissingPath(null)}
        />
      )}
    </div>
  )
}

import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  CheckCircle,
  Circle,
  AlertCircle,
  Clock,
  ChevronRight,
} from 'lucide-react'
import { api } from '../services/api'
import { ChecklistPhase, ChecklistStatus } from '../types'

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

  const { data: summaryData, isLoading: summaryLoading } = useQuery({
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

  const phases = Object.values(ChecklistPhase)

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
            const canProceed = summary?.can_proceed ?? false

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
                {summaryData[expandedPhase].completed_items} of{' '}
                {summaryData[expandedPhase].total_items} items complete
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
                  <li key={item.code} className="px-5 py-4 hover:bg-gray-50">
                    <div className="flex items-start gap-4">
                      <div className={`p-2 rounded-lg ${config.bg}`}>
                        <StatusIcon className={`h-5 w-5 ${config.color}`} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium text-gray-500">
                            {item.code}
                          </span>
                          <span className={`badge ${config.bg} ${config.color}`}>
                            {config.label}
                          </span>
                        </div>
                        <p className="mt-1 font-medium text-gray-900">{item.name}</p>
                        <div className="mt-2 flex items-center gap-4 text-sm text-gray-500">
                          <span>
                            Required paths: {item.required_paths_covered}/
                            {item.required_paths_total}
                          </span>
                        </div>
                        {item.blocking_issues && item.blocking_issues.length > 0 && (
                          <div className="mt-2 text-sm text-red-600">
                            <AlertCircle className="inline h-4 w-4 mr-1" />
                            {item.blocking_issues.join(', ')}
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

      {/* Gaps Summary */}
      <div className="card p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Evidence Gaps</h2>
        <p className="text-sm text-gray-500">
          View the Readiness page for detailed gap analysis and improvement
          suggestions.
        </p>
      </div>
    </div>
  )
}

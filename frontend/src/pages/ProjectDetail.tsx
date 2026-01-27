import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  FileCheck,
  ClipboardList,
  Gauge,
  Upload,
  AlertCircle,
  CheckCircle,
  Clock,
} from 'lucide-react'
import { api } from '../services/api'

export default function ProjectDetail() {
  const { projectId } = useParams<{ projectId: string }>()

  const { data: project, isLoading } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => api.getProject(projectId!),
    enabled: !!projectId,
  })

  if (isLoading) {
    return <div className="text-center py-12 text-gray-500">Loading project...</div>
  }

  if (!project) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">Project not found</h3>
      </div>
    )
  }

  const quickActions = [
    {
      name: 'Facts Review',
      description: `${project.approved_fact_count} approved / ${project.fact_count} total`,
      href: `/projects/${projectId}/facts`,
      icon: FileCheck,
      color: 'bg-blue-500',
    },
    {
      name: 'Checklist',
      description: 'Track diligence progress',
      href: `/projects/${projectId}/checklist`,
      icon: ClipboardList,
      color: 'bg-purple-500',
    },
    {
      name: 'Readiness',
      description: project.overall_readiness_score
        ? `Score: ${project.overall_readiness_score.toFixed(1)}/10`
        : 'Not yet scored',
      href: `/projects/${projectId}/readiness`,
      icon: Gauge,
      color: 'bg-green-500',
    },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">{project.name}</h1>
        <p className="mt-1 text-sm text-gray-500">{project.issuer_name}</p>
      </div>

      {/* Project Info */}
      <div className="card p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Project Details</h2>
        <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <div>
            <dt className="text-sm text-gray-500">Location</dt>
            <dd className="mt-1 font-medium text-gray-900">
              {project.project_location || '—'}
            </dd>
          </div>
          <div>
            <dt className="text-sm text-gray-500">Target Bond Amount</dt>
            <dd className="mt-1 font-medium text-gray-900">
              {project.target_bond_amount
                ? `$${project.target_bond_amount.toLocaleString()}`
                : '—'}
            </dd>
          </div>
          <div>
            <dt className="text-sm text-gray-500">Artifacts</dt>
            <dd className="mt-1 font-medium text-gray-900">{project.artifact_count}</dd>
          </div>
          <div>
            <dt className="text-sm text-gray-500">Total Facts</dt>
            <dd className="mt-1 font-medium text-gray-900">{project.fact_count}</dd>
          </div>
          <div>
            <dt className="text-sm text-gray-500">Approved Facts</dt>
            <dd className="mt-1 font-medium text-gray-900">
              {project.approved_fact_count}
            </dd>
          </div>
          <div>
            <dt className="text-sm text-gray-500">Readiness Score</dt>
            <dd className="mt-1 font-medium text-gray-900">
              {project.overall_readiness_score?.toFixed(1) ?? 'Not calculated'}
            </dd>
          </div>
        </dl>
        {project.description && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <dt className="text-sm text-gray-500">Description</dt>
            <dd className="mt-1 text-gray-900">{project.description}</dd>
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          {quickActions.map((action) => (
            <Link
              key={action.name}
              to={action.href}
              className="card p-5 hover:shadow-md transition-shadow"
            >
              <div className="flex items-center gap-4">
                <div className={`${action.color} rounded-lg p-3`}>
                  <action.icon className="h-6 w-6 text-white" />
                </div>
                <div>
                  <p className="font-medium text-gray-900">{action.name}</p>
                  <p className="text-sm text-gray-500">{action.description}</p>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </div>

      {/* Upload Section */}
      <div className="card p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Upload Documents</h2>
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-primary-400 transition-colors">
          <Upload className="mx-auto h-12 w-12 text-gray-400" />
          <p className="mt-2 text-sm font-medium text-gray-900">
            Drag and drop files here
          </p>
          <p className="mt-1 text-sm text-gray-500">
            or click to browse (PDF, DOCX, XLSX, CSV)
          </p>
          <input
            type="file"
            className="hidden"
            accept=".pdf,.docx,.xlsx,.xls,.csv"
            multiple
          />
        </div>
      </div>

      {/* Activity Summary */}
      <div className="card">
        <div className="border-b border-gray-200 px-5 py-4">
          <h2 className="text-lg font-medium text-gray-900">Recent Activity</h2>
        </div>
        <div className="p-5">
          <div className="flex items-center gap-3 text-sm text-gray-500">
            <Clock className="h-4 w-4" />
            <span>
              Last updated:{' '}
              {new Date(project.updated_at).toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
              })}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}

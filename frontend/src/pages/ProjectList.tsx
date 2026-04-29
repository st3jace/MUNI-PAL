import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Plus, FolderKanban, Trash2 } from 'lucide-react'
import { api } from '../services/api'
import type { ProjectCreate } from '../types'

const getErrorMessage = (error: unknown): string => {
  if (error instanceof Error && error.message) {
    return error.message
  }
  return 'Request failed. Check API connectivity and auth token configuration.'
}

export default function ProjectList() {
  const [showCreateModal, setShowCreateModal] = useState(false)
  const queryClient = useQueryClient()

  const { data, isLoading, error: listError } = useQuery({
    queryKey: ['projects'],
    queryFn: () => api.listProjects(),
  })

  const createMutation = useMutation({
    mutationFn: (project: ProjectCreate) => api.createProject(project),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      setShowCreateModal(false)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (projectId: string) => api.deleteProject(projectId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
  })

  const sectorOptions = [
    { value: 'healthcare', label: 'Healthcare', subsectors: [
      { value: 'healthcare_hospital', label: 'Hospital / Health System' },
      { value: 'healthcare_senior_living', label: 'Senior Living / CCRC' },
      { value: 'healthcare_fqhc_bond', label: 'FQHC Revenue Bond' },
      { value: 'healthcare_fqhc_cdfi', label: 'FQHC CDFI / NMTC' },
    ]},
    { value: 'housing', label: 'Affordable Housing', subsectors: [
      { value: 'housing_affordable_multifamily', label: 'Affordable Multifamily' },
    ]},
    { value: 'waste', label: 'Waste-to-Energy', subsectors: [
      { value: 'waste_to_energy', label: 'Waste-to-Energy / UCS' },
    ]},
  ]

  const [selectedSector, setSelectedSector] = useState('')

  const handleCreate = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const formData = new FormData(e.currentTarget)
    const sector = formData.get('sector') as string
    const subsector = formData.get('subsector') as string || undefined
    createMutation.mutate({
      name: formData.get('name') as string,
      sector,
      subsector,
      issuer_name: formData.get('issuer_name') as string,
      description: formData.get('description') as string || undefined,
      project_location: formData.get('project_location') as string || undefined,
      target_bond_amount: formData.get('target_bond_amount')
        ? Number(formData.get('target_bond_amount'))
        : undefined,
    })
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Projects</h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage your bond-eligible project workspaces
          </p>
        </div>
        <button onClick={() => setShowCreateModal(true)} className="btn-primary">
          <Plus className="h-4 w-4 mr-2" />
          New Project
        </button>
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-gray-500">Loading projects...</div>
      ) : listError ? (
        <div className="card p-6 border border-red-200 bg-red-50 text-red-700">
          {getErrorMessage(listError)}
        </div>
      ) : data?.projects.length === 0 ? (
        <div className="card p-12 text-center">
          <FolderKanban className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No projects</h3>
          <p className="mt-1 text-sm text-gray-500">
            Get started by creating a new project.
          </p>
          <div className="mt-4">
            <button onClick={() => setShowCreateModal(true)} className="btn-primary">
              <Plus className="h-4 w-4 mr-2" />
              New Project
            </button>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {data?.projects.map((project) => (
            <div key={project.id} className="card hover:shadow-md transition-shadow">
              <div className="p-5">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <Link
                      to={`/projects/${project.id}`}
                      className="block font-medium text-gray-900 truncate hover:text-primary-600"
                    >
                      {project.name}
                    </Link>
                    <p className="mt-1 text-sm text-gray-500 truncate">
                      {project.issuer_name}
                    </p>
                    {project.sector && (
                      <span className="mt-1 inline-block rounded-full bg-primary-50 px-2 py-0.5 text-xs font-medium text-primary-700">
                        {project.sector}{project.subsector ? ` / ${project.subsector.replace(`${project.sector}_`, '')}` : ''}
                      </span>
                    )}
                  </div>
                  <button
                    onClick={() => {
                      if (confirm('Delete this project?')) {
                        deleteMutation.mutate(project.id)
                      }
                    }}
                    className="ml-2 p-1 text-gray-400 hover:text-red-500"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>

                <div className="mt-4 flex items-center justify-between text-sm">
                  <div>
                    <span className="text-gray-500">Artifacts:</span>{' '}
                    <span className="font-medium">{project.artifact_count}</span>
                  </div>
                  {project.overall_readiness_score !== null && (
                    <div>
                      <span className="text-gray-500">Readiness:</span>{' '}
                      <span className="font-medium">
                        {project.overall_readiness_score?.toFixed(1) ?? '—'}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex min-h-screen items-center justify-center p-4">
            <div
              className="fixed inset-0 bg-gray-500 bg-opacity-75"
              onClick={() => setShowCreateModal(false)}
            />
            <div className="relative bg-white rounded-lg shadow-xl max-w-md w-full p-6">
              <h2 className="text-lg font-medium text-gray-900 mb-4">
                Create New Project
              </h2>
              <form onSubmit={handleCreate} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Project Name *
                  </label>
                  <input
                    type="text"
                    name="name"
                    required
                    className="mt-1 input"
                    placeholder="e.g., Oakport Regional Medical Center"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Sector *
                  </label>
                  <select
                    name="sector"
                    required
                    className="mt-1 input"
                    value={selectedSector}
                    onChange={(e) => setSelectedSector(e.target.value)}
                  >
                    <option value="">Select sector...</option>
                    {sectorOptions.map((s) => (
                      <option key={s.value} value={s.value}>{s.label}</option>
                    ))}
                  </select>
                </div>
                {sectorOptions.find((s) => s.value === selectedSector)?.subsectors.length ? (
                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Sub-Sector
                    </label>
                    <select name="subsector" className="mt-1 input">
                      <option value="">Select sub-sector...</option>
                      {sectorOptions.find((s) => s.value === selectedSector)?.subsectors.map((ss) => (
                        <option key={ss.value} value={ss.value}>{ss.label}</option>
                      ))}
                    </select>
                  </div>
                ) : null}
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Issuer Name *
                  </label>
                  <input
                    type="text"
                    name="issuer_name"
                    required
                    className="mt-1 input"
                    placeholder="e.g., Oakport Health Authority"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Description
                  </label>
                  <textarea
                    name="description"
                    rows={3}
                    className="mt-1 input"
                    placeholder="Brief project description..."
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Location
                  </label>
                  <input
                    type="text"
                    name="project_location"
                    className="mt-1 input"
                    placeholder="e.g., Oakport, OH"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Target Bond Amount ($)
                  </label>
                  <input
                    type="number"
                    name="target_bond_amount"
                    className="mt-1 input"
                    placeholder="e.g., 50000000"
                  />
                </div>
                <div className="flex justify-end gap-3 pt-4">
                  <button
                    type="button"
                    onClick={() => setShowCreateModal(false)}
                    className="btn-secondary"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={createMutation.isPending}
                    className="btn-primary"
                  >
                    {createMutation.isPending ? 'Creating...' : 'Create Project'}
                  </button>
                </div>
                {createMutation.error ? (
                  <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                    {getErrorMessage(createMutation.error)}
                  </div>
                ) : null}
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

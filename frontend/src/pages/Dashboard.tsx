import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { FolderKanban, FileCheck, AlertCircle, TrendingUp } from 'lucide-react'
import { api } from '../services/api'

export default function Dashboard() {
  const { data: projectsData, isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: () => api.listProjects({ limit: 5 }),
  })

  const stats = [
    {
      name: 'Total Projects',
      value: projectsData?.total ?? 0,
      icon: FolderKanban,
      color: 'bg-blue-500',
    },
    {
      name: 'Facts Pending Review',
      value: '—',
      icon: FileCheck,
      color: 'bg-yellow-500',
    },
    {
      name: 'Critical Gaps',
      value: '—',
      icon: AlertCircle,
      color: 'bg-red-500',
    },
    {
      name: 'Avg Readiness',
      value: '—',
      icon: TrendingUp,
      color: 'bg-green-500',
    },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-1 text-sm text-gray-500">
          Overview of your bond facility management activities
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <div key={stat.name} className="card p-5">
            <div className="flex items-center">
              <div className={`${stat.color} rounded-md p-3`}>
                <stat.icon className="h-6 w-6 text-white" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">{stat.name}</p>
                <p className="text-2xl font-semibold text-gray-900">{stat.value}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Recent Projects */}
      <div className="card">
        <div className="border-b border-gray-200 px-5 py-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-medium text-gray-900">Recent Projects</h2>
            <Link to="/projects" className="text-sm text-primary-600 hover:text-primary-700">
              View all
            </Link>
          </div>
        </div>

        {isLoading ? (
          <div className="p-5 text-center text-gray-500">Loading...</div>
        ) : projectsData?.projects.length === 0 ? (
          <div className="p-5 text-center">
            <FolderKanban className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No projects</h3>
            <p className="mt-1 text-sm text-gray-500">
              Get started by creating a new project.
            </p>
            <div className="mt-4">
              <Link to="/projects" className="btn-primary">
                Create Project
              </Link>
            </div>
          </div>
        ) : (
          <ul className="divide-y divide-gray-200">
            {projectsData?.projects.map((project) => (
              <li key={project.id}>
                <Link
                  to={`/projects/${project.id}`}
                  className="flex items-center justify-between px-5 py-4 hover:bg-gray-50"
                >
                  <div>
                    <p className="font-medium text-gray-900">{project.name}</p>
                    <p className="text-sm text-gray-500">{project.issuer_name}</p>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <p className="text-sm text-gray-500">Artifacts</p>
                      <p className="font-medium">{project.artifact_count}</p>
                    </div>
                    {project.overall_readiness_score !== null && (
                      <div className="text-right">
                        <p className="text-sm text-gray-500">Readiness</p>
                        <p className="font-medium">
                          {project.overall_readiness_score?.toFixed(1) ?? '—'}
                        </p>
                      </div>
                    )}
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}

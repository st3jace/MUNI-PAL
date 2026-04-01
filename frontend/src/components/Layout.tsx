import { Outlet, NavLink, useParams } from 'react-router-dom'
import {
  LayoutDashboard,
  FolderKanban,
  FileCheck,
  ClipboardList,
  Gauge,
  FileOutput,
  Menu,
  X,
  // v2 icons
  FileText,
  MessageSquareMore,
  Package,
  // Sensing tools
  Wrench,
} from 'lucide-react'
import { useState } from 'react'
import AdvisorChat from './AdvisorChat'

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Projects', href: '/projects', icon: FolderKanban },
  { name: 'Sensing Tools', href: '/tools', icon: Wrench },
]

const projectNavigation = [
  { name: 'Overview', href: '', icon: FolderKanban },
  { name: 'Facts Review', href: '/facts', icon: FileCheck },
  { name: 'Checklist', href: '/checklist', icon: ClipboardList },
  { name: 'Readiness', href: '/readiness', icon: Gauge },
  { name: 'Hand-Off Pack', href: '/handoff', icon: FileOutput },
  // v2 - WP7, WP8, Bifurcated Deliverables
  { name: 'Disclosure', href: '/disclosure', icon: FileText },
  { name: 'Info Requests', href: '/requests', icon: MessageSquareMore },
  { name: 'Advisory Packages', href: '/packages', icon: Package },
]

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const { projectId } = useParams()

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-gray-600 bg-opacity-75 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div
        className={`fixed inset-y-0 left-0 z-50 w-64 bg-muni-navy transform transition-transform lg:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex h-16 items-center justify-between px-4">
          <div className="flex items-center gap-3">
            <img
              src="/muni-pal-emblem.png"
              alt="Muni-Pal"
              className="h-9 w-9 rounded-lg object-contain"
              style={{ filter: 'drop-shadow(0 1px 4px rgba(0,0,0,0.3))' }}
            />
            <span className="text-white font-semibold text-lg">Muni-Pal</span>
          </div>
          <button
            className="lg:hidden text-white"
            onClick={() => setSidebarOpen(false)}
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        <nav className="mt-4 px-2">
          <div className="space-y-1">
            {navigation.map((item) => (
              <NavLink
                key={item.name}
                to={item.href}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-primary-700 text-white'
                      : 'text-gray-300 hover:bg-primary-800 hover:text-white'
                  }`
                }
              >
                <item.icon className="h-5 w-5" />
                {item.name}
              </NavLink>
            ))}
          </div>

          {projectId && (
            <>
              <div className="mt-8 mb-2 px-3">
                <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                  Project
                </h3>
              </div>
              <div className="space-y-1">
                {projectNavigation.map((item) => (
                  <NavLink
                    key={item.name}
                    to={`/projects/${projectId}${item.href}`}
                    end={item.href === ''}
                    className={({ isActive }) =>
                      `flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                        isActive
                          ? 'bg-primary-700 text-white'
                          : 'text-gray-300 hover:bg-primary-800 hover:text-white'
                      }`
                    }
                  >
                    <item.icon className="h-5 w-5" />
                    {item.name}
                  </NavLink>
                ))}
              </div>
            </>
          )}
        </nav>
      </div>

      {/* Main content */}
      <div className="lg:pl-64">
        {/* Top bar */}
        <div className="sticky top-0 z-40 flex h-16 items-center gap-4 border-b border-gray-200 bg-white px-4 shadow-sm">
          <button
            className="lg:hidden text-gray-500"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="h-6 w-6" />
          </button>
          <div className="flex-1" />
          <span className="text-sm text-gray-500">Bond Facility Management System</span>
        </div>

        {/* Page content */}
        <main className="p-6">
          <Outlet />
        </main>

        {/* Footer */}
        <footer className="border-t border-gray-200 bg-white px-6 py-4">
          <div className="flex items-center justify-center gap-2">
            <img
              src="/muni-pal-emblem.png"
              alt="Muni-Pal"
              className="h-6 w-6 rounded object-contain opacity-50"
            />
            <p className="text-sm text-gray-500">
              Muni-Pal — A Launch Shop product. Built by Innovation Factory.
            </p>
          </div>
        </footer>
      </div>

      {/* Municipal Advisor Chat Widget */}
      <AdvisorChat />
    </div>
  )
}

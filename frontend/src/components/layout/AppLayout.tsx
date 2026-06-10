import { Outlet, NavLink } from 'react-router-dom'
import {
  LayoutDashboard, Bot, Zap, FlaskConical,
  GitBranch, BarChart3, AlertTriangle, Settings,
} from 'lucide-react'
import { clsx } from 'clsx'

const NAV_ITEMS = [
  { to: '/dashboard',   label: 'Dashboard',   icon: LayoutDashboard },
  { to: '/agents',      label: 'Agents',       icon: Bot },
  { to: '/executions',  label: 'Executions',   icon: Zap },
  { to: '/evaluations', label: 'Evaluations',  icon: FlaskConical },
  { to: '/analytics',   label: 'Analytics',    icon: BarChart3 },
  { to: '/failures',    label: 'Failures',     icon: AlertTriangle },
]

export function AppLayout() {
  return (
    <div className="flex h-screen bg-gray-950">
      {/* Sidebar */}
      <aside className="w-60 flex-shrink-0 flex flex-col bg-gray-900 border-r border-gray-800">
        {/* Logo */}
        <div className="flex items-center gap-3 px-6 py-5 border-b border-gray-800">
          <div className="w-8 h-8 bg-brand-600 rounded-lg flex items-center justify-center">
            <GitBranch className="w-4 h-4 text-white" />
          </div>
          <div>
            <p className="text-sm font-semibold text-white leading-tight">Agent Platform</p>
            <p className="text-xs text-gray-400">Reliability Suite</p>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-1">
          {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-brand-600/20 text-brand-400'
                    : 'text-gray-400 hover:text-gray-100 hover:bg-gray-800',
                )
              }
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="px-3 py-4 border-t border-gray-800">
          <NavLink
            to="/settings"
            className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-gray-400 hover:text-gray-100 hover:bg-gray-800 transition-colors"
          >
            <Settings className="w-4 h-4" />
            Settings
          </NavLink>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  )
}

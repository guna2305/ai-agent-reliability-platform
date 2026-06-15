import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, Bot, Zap, FlaskConical,
  GitBranch, BarChart3, AlertTriangle, LogOut,
} from 'lucide-react'
import { clsx } from 'clsx'
import { authApi } from '@/api/auth'
import { useAuthStore } from '@/stores/authStore'
import { useOrgStore } from '@/stores/orgStore'

const NAV_ITEMS = [
  { to: '/dashboard',   label: 'Dashboard',   icon: LayoutDashboard },
  { to: '/agents',      label: 'Agents',       icon: Bot },
  { to: '/executions',  label: 'Executions',   icon: Zap },
  { to: '/evaluations', label: 'Evaluations',  icon: FlaskConical },
  { to: '/analytics',   label: 'Analytics',    icon: BarChart3 },
  { to: '/failures',    label: 'Failures',     icon: AlertTriangle },
]

export function AppLayout() {
  const navigate = useNavigate()
  const user = useAuthStore((s) => s.user)
  const clear = useAuthStore((s) => s.clear)
  const currentOrg = useOrgStore((s) => s.currentOrg)
  const organizations = useOrgStore((s) => s.organizations)
  const setCurrentOrg = useOrgStore((s) => s.setCurrentOrg)

  const logout = async () => {
    try {
      await authApi.logout(localStorage.getItem('refresh_token'))
    } catch {
      /* ignore — clear locally regardless */
    }
    clear()
    navigate('/login')
  }

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

        {/* Org switcher */}
        {organizations.length > 0 && (
          <div className="px-4 py-3 border-b border-gray-800">
            <label className="text-xs text-gray-500 font-medium">Organization</label>
            <select
              value={currentOrg?.slug ?? ''}
              onChange={(e) => {
                const org = organizations.find((o) => o.slug === e.target.value)
                if (org) setCurrentOrg(org)
              }}
              className="mt-1 w-full bg-gray-950 border border-gray-700 rounded-lg px-2 py-1.5 text-sm text-white focus:outline-none focus:border-brand-500"
            >
              {organizations.map((o) => (
                <option key={o.id} value={o.slug}>{o.name}</option>
              ))}
            </select>
          </div>
        )}

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

        {/* Footer — user + logout */}
        <div className="px-3 py-4 border-t border-gray-800">
          {user && (
            <div className="px-3 pb-2">
              <p className="text-sm text-gray-200 font-medium truncate">{user.full_name}</p>
              <p className="text-xs text-gray-500 truncate">{user.email}</p>
            </div>
          )}
          <button
            onClick={logout}
            className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-gray-400 hover:text-gray-100 hover:bg-gray-800 transition-colors w-full"
          >
            <LogOut className="w-4 h-4" />
            Sign out
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  )
}

import { Outlet, NavLink } from 'react-router-dom'
import {
  Snowflake,
  LayoutDashboard,
  Columns2,
  Users,
  ScrollText,
  ClipboardList,
  BookLock,
  Wifi,
  WifiOff,
} from 'lucide-react'
import { useDashboardStore } from '../store'

function Layout() {
  const { connected, colony } = useDashboardStore()

  const navItems = [
    { to: '/', icon: LayoutDashboard, label: 'Operations Center', end: true },
    { to: '/board', icon: Columns2, label: 'Job Board' },
    { to: '/workers', icon: Users, label: 'Field Team' },
    { to: '/requests', icon: ClipboardList, label: 'Service Requests' },
    { to: '/events', icon: ScrollText, label: 'Activity Feed' },
    { to: '/ledger', icon: BookLock, label: 'Agent Ledger' },
  ]

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-50">
        <div className="max-w-screen-2xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <Snowflake className="w-5 h-5 text-white" />
              </div>
              <div>
                <span className="text-xl font-bold text-slate-800">CoolFlow</span>
                {colony && (
                  <span className="text-sm text-slate-400 ml-2">/ {colony.name}</span>
                )}
              </div>
            </div>

            {/* Status */}
            <div className="flex items-center gap-2">
              {connected ? (
                <>
                  <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                  <Wifi className="w-4 h-4 text-green-500" />
                  <span className="text-sm text-green-600 font-medium">Live</span>
                </>
              ) : (
                <>
                  <WifiOff className="w-4 h-4 text-red-500" />
                  <span className="text-sm text-red-600">Disconnected</span>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar */}
        <nav className="w-56 bg-white border-r border-slate-200 min-h-[calc(100vh-4rem)] p-3 flex-shrink-0">
          <ul className="space-y-1">
            {navItems.map(({ to, icon: Icon, label, end }) => (
              <li key={to}>
                <NavLink
                  to={to}
                  end={end}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-blue-50 text-blue-700'
                        : 'text-slate-600 hover:bg-slate-50 hover:text-slate-800'
                    }`
                  }
                >
                  <Icon className="w-4 h-4 flex-shrink-0" />
                  {label}
                </NavLink>
              </li>
            ))}
          </ul>

          {/* Colony Status */}
          {colony && (
            <div className="mt-6 mx-1 p-3 bg-slate-50 rounded-lg border border-slate-200">
              <p className="text-xs font-medium text-slate-500 mb-2">Colony Status</p>
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${
                  colony.status === 'running' ? 'bg-green-500' : 'bg-slate-400'
                }`} />
                <span className="text-xs text-slate-700 capitalize">{colony.status}</span>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                {colony.workers.length} agents active
              </p>
            </div>
          )}
        </nav>

        {/* Main Content */}
        <main className="flex-1 p-6 min-w-0">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

export default Layout

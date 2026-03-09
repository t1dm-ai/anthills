import { Outlet, NavLink } from 'react-router-dom'
import { Bug, LayoutDashboard, Grid3X3, Users, ScrollText, Wifi, WifiOff } from 'lucide-react'
import { useDashboardStore } from '../store'

function Layout() {
  const { connected, colony } = useDashboardStore()
  
  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <div className="flex items-center gap-3">
              <Bug className="w-8 h-8 text-amber-700" />
              <span className="text-xl font-bold text-slate-800">Anthills</span>
              {colony && (
                <span className="text-sm text-slate-500 ml-2">
                  / {colony.name}
                </span>
              )}
            </div>
            
            {/* Connection Status */}
            <div className="flex items-center gap-2">
              {connected ? (
                <>
                  <Wifi className="w-4 h-4 text-green-500" />
                  <span className="text-sm text-green-600">Connected</span>
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
        <nav className="w-64 bg-white border-r border-slate-200 min-h-[calc(100vh-4rem)] p-4">
          <ul className="space-y-1">
            <li>
              <NavLink
                to="/"
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-amber-50 text-amber-700'
                      : 'text-slate-600 hover:bg-slate-50'
                  }`
                }
              >
                <LayoutDashboard className="w-5 h-5" />
                Dashboard
              </NavLink>
            </li>
            <li>
              <NavLink
                to="/board"
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-amber-50 text-amber-700'
                      : 'text-slate-600 hover:bg-slate-50'
                  }`
                }
              >
                <Grid3X3 className="w-5 h-5" />
                Pheromone Board
              </NavLink>
            </li>
            <li>
              <NavLink
                to="/workers"
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-amber-50 text-amber-700'
                      : 'text-slate-600 hover:bg-slate-50'
                  }`
                }
              >
                <Users className="w-5 h-5" />
                Workers
              </NavLink>
            </li>
            <li>
              <NavLink
                to="/events"
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-amber-50 text-amber-700'
                      : 'text-slate-600 hover:bg-slate-50'
                  }`
                }
              >
                <ScrollText className="w-5 h-5" />
                Event Log
              </NavLink>
            </li>
          </ul>
        </nav>
        
        {/* Main Content */}
        <main className="flex-1 p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

export default Layout

import { useDashboardStore } from '../store'
import { Bug, Droplets, Zap, Clock, AlertCircle, CheckCircle } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import type { FC, ComponentType } from 'react'

interface StatCardProps {
  title: string
  value: string | number
  icon: ComponentType<{ className?: string }>
  color: string
}

const StatCard: FC<StatCardProps> = ({ title, value, icon: Icon, color }) => {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-slate-500">{title}</p>
          <p className="text-2xl font-bold text-slate-800 mt-1">{value}</p>
        </div>
        <div className={`p-3 rounded-lg ${color}`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
      </div>
    </div>
  )
}

function Dashboard() {
  const { boardStats, workerStats, events, colony } = useDashboardStore()

  const recentEvents = events.slice(0, 5)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Dashboard</h1>
        <p className="text-slate-500 mt-1">
          Real-time overview of your colony
        </p>
      </div>
      
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Workers"
          value={workerStats.total_workers}
          icon={Bug}
          color="bg-amber-500"
        />
        <StatCard
          title="Active Pheromones"
          value={boardStats.active_pheromones}
          icon={Droplets}
          color="bg-emerald-500"
        />
        <StatCard
          title="Events"
          value={events.length}
          icon={Zap}
          color="bg-blue-500"
        />
        <StatCard
          title="Uptime"
          value={colony?.started_at ? formatDistanceToNow(new Date(colony.started_at)) : '-'}
          icon={Clock}
          color="bg-purple-500"
        />
      </div>
      
      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Worker Status */}
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <h2 className="text-lg font-semibold text-slate-800 mb-4">Worker Status</h2>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-green-500" />
                <span className="text-slate-600">Busy</span>
              </div>
              <span className="font-semibold text-slate-800">{workerStats.busy_workers}</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-slate-400" />
                <span className="text-slate-600">Idle</span>
              </div>
              <span className="font-semibold text-slate-800">{workerStats.idle_workers}</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-red-500" />
                <span className="text-slate-600">Errors</span>
              </div>
              <span className="font-semibold text-slate-800">{workerStats.error_workers}</span>
            </div>
          </div>
          
          {/* Progress Bar */}
          <div className="mt-6">
            <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-green-500 transition-all duration-300"
                style={{ 
                  width: workerStats.total_workers > 0 
                    ? `${(workerStats.busy_workers / workerStats.total_workers) * 100}%` 
                    : '0%' 
                }}
              />
            </div>
            <p className="text-sm text-slate-500 mt-2">
              {workerStats.total_workers > 0 
                ? `${Math.round((workerStats.busy_workers / workerStats.total_workers) * 100)}% utilization`
                : 'No workers registered'
              }
            </p>
          </div>
        </div>
        
        {/* Recent Activity */}
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <h2 className="text-lg font-semibold text-slate-800 mb-4">Recent Activity</h2>
          <div className="space-y-3">
            {recentEvents.length === 0 ? (
              <p className="text-slate-500 text-sm">No events yet</p>
            ) : (
              recentEvents.map((event) => (
                <div key={event.id} className="flex items-start gap-3 text-sm">
                  {event.event_type === 'deposit' ? (
                    <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                  ) : event.event_type === 'evaporated' ? (
                    <AlertCircle className="w-4 h-4 text-orange-500 mt-0.5 flex-shrink-0" />
                  ) : (
                    <Zap className="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0" />
                  )}
                  <div className="flex-1 min-w-0">
                    <p className="text-slate-800 truncate">
                      {event.event_type === 'deposit' ? 'Pheromone deposited' : 'Pheromone evaporated'}
                      {event.pheromone && (
                        <span className="text-slate-500"> → {event.pheromone.type}</span>
                      )}
                    </p>
                    <p className="text-slate-400 text-xs">
                      {formatDistanceToNow(new Date(event.timestamp), { addSuffix: true })}
                    </p>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
      
      {/* Colony Info */}
      {colony && (
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <h2 className="text-lg font-semibold text-slate-800 mb-4">Colony Information</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-slate-500">Name</p>
              <p className="font-medium text-slate-800">{colony.name}</p>
            </div>
            <div>
              <p className="text-sm text-slate-500">Status</p>
              <p className={`font-medium ${
                colony.status === 'running' ? 'text-green-600' : 
                colony.status === 'stopped' ? 'text-red-600' : 'text-slate-600'
              }`}>
                {colony.status.charAt(0).toUpperCase() + colony.status.slice(1)}
              </p>
            </div>
            <div>
              <p className="text-sm text-slate-500">Started</p>
              <p className="font-medium text-slate-800">
                {colony.started_at ? new Date(colony.started_at).toLocaleTimeString() : '-'}
              </p>
            </div>
            <div>
              <p className="text-sm text-slate-500">Pheromones</p>
              <p className="font-medium text-slate-800">
                {colony.pheromone_count}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Dashboard

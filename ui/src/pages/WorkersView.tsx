import { useDashboardStore } from '../store'
import { Bug, Clock, CheckCircle, XCircle, Loader2, Tag, Pause } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import type { Worker } from '../types'

function WorkerCard({ worker }: { worker: Worker }) {
  const statusColors = {
    idle: 'bg-slate-100 text-slate-600',
    busy: 'bg-emerald-100 text-emerald-700',
    error: 'bg-red-100 text-red-700',
  }
  
  const statusIcons = {
    idle: Pause,
    busy: Loader2,
    error: XCircle,
  }
  
  const StatusIcon = statusIcons[worker.status]
  
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={`
            w-10 h-10 rounded-lg flex items-center justify-center
            ${worker.status === 'busy' ? 'bg-amber-100' : 
              worker.status === 'error' ? 'bg-red-100' : 'bg-slate-100'}
          `}>
            <Bug className={`w-5 h-5 ${
              worker.status === 'busy' ? 'text-amber-600' : 
              worker.status === 'error' ? 'text-red-600' : 'text-slate-500'
            }`} />
          </div>
          <div>
            <h3 className="font-semibold text-slate-800">{worker.name}</h3>
            <p className="text-sm text-slate-500 font-mono">{worker.reacts_to}</p>
          </div>
        </div>
        
        <span className={`
          inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium
          ${statusColors[worker.status]}
        `}>
          <StatusIcon className={`w-3 h-3 ${worker.status === 'busy' ? 'animate-spin' : ''}`} />
          {worker.status}
        </span>
      </div>
      
      {/* Subscription Pattern */}
      <div className="mb-4">
        <p className="text-xs text-slate-500 mb-2">Reacts to</p>
        <div className="flex flex-wrap gap-1.5">
          <span className="inline-flex items-center gap-1 px-2 py-1 bg-slate-100 rounded text-xs font-mono text-slate-600">
            <Tag className="w-3 h-3" />
            {worker.reacts_to}
          </span>
        </div>
      </div>
      
      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 pt-4 border-t border-slate-100">
        <div>
          <p className="text-xs text-slate-500">Completed</p>
          <p className="text-lg font-semibold text-slate-800 flex items-center gap-1">
            <CheckCircle className="w-4 h-4 text-green-500" />
            {worker.processed_count}
          </p>
        </div>
        <div>
          <p className="text-xs text-slate-500">Errors</p>
          <p className="text-lg font-semibold text-slate-800 flex items-center gap-1">
            <XCircle className="w-4 h-4 text-red-500" />
            {worker.error_count}
          </p>
        </div>
        <div>
          <p className="text-xs text-slate-500">Last Active</p>
          <p className="text-xs text-slate-600 flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {worker.last_active 
              ? formatDistanceToNow(new Date(worker.last_active), { addSuffix: true })
              : 'Never'
            }
          </p>
        </div>
      </div>
    </div>
  )
}

function WorkersView() {
  const { workers, workerStats } = useDashboardStore()

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Workers</h1>
        <p className="text-slate-500 mt-1">
          Monitor your colony's worker agents
        </p>
      </div>
      
      {/* Summary Stats */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-white rounded-lg border border-slate-200 p-4 flex items-center gap-4">
          <div className="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center">
            <Bug className="w-5 h-5 text-amber-600" />
          </div>
          <div>
            <p className="text-2xl font-bold text-slate-800">{workerStats.total_workers}</p>
            <p className="text-sm text-slate-500">Total</p>
          </div>
        </div>
        
        <div className="bg-white rounded-lg border border-slate-200 p-4 flex items-center gap-4">
          <div className="w-10 h-10 rounded-lg bg-emerald-100 flex items-center justify-center">
            <Loader2 className="w-5 h-5 text-emerald-600 animate-spin" />
          </div>
          <div>
            <p className="text-2xl font-bold text-slate-800">{workerStats.busy_workers}</p>
            <p className="text-sm text-slate-500">Busy</p>
          </div>
        </div>
        
        <div className="bg-white rounded-lg border border-slate-200 p-4 flex items-center gap-4">
          <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center">
            <Pause className="w-5 h-5 text-slate-500" />
          </div>
          <div>
            <p className="text-2xl font-bold text-slate-800">{workerStats.idle_workers}</p>
            <p className="text-sm text-slate-500">Idle</p>
          </div>
        </div>
        
        <div className="bg-white rounded-lg border border-slate-200 p-4 flex items-center gap-4">
          <div className="w-10 h-10 rounded-lg bg-red-100 flex items-center justify-center">
            <XCircle className="w-5 h-5 text-red-500" />
          </div>
          <div>
            <p className="text-2xl font-bold text-slate-800">{workerStats.error_workers}</p>
            <p className="text-sm text-slate-500">Errors</p>
          </div>
        </div>
      </div>
      
      {/* Workers Grid */}
      {workers.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
          <div className="w-12 h-12 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Bug className="w-6 h-6 text-slate-400" />
          </div>
          <h3 className="text-lg font-medium text-slate-800 mb-1">No workers</h3>
          <p className="text-slate-500">
            Workers will appear here when the colony starts
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {workers.map(worker => (
            <WorkerCard key={worker.id} worker={worker} />
          ))}
        </div>
      )}
    </div>
  )
}

export default WorkersView

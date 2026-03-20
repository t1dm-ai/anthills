import { useMemo } from 'react'
import { useDashboardStore } from '../store'
import {
  Snowflake,
  Thermometer,
  Wrench,
  Zap,
  MapPin,
  User,
  Clock,
} from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import type { Pheromone } from '../types'
import type { JobPayload, IssueType } from '../types'
import type { ComponentType } from 'react'

const COLUMNS = [
  { type: 'job.requested', label: 'New Request', color: 'blue', dot: 'bg-blue-500', header: 'bg-blue-50 border-blue-200' },
  { type: 'job.qualified', label: 'Qualified', color: 'amber', dot: 'bg-amber-500', header: 'bg-amber-50 border-amber-200' },
  { type: 'job.dispatched', label: 'Dispatched', color: 'purple', dot: 'bg-purple-500', header: 'bg-purple-50 border-purple-200' },
  { type: 'job.on_site', label: 'On Site', color: 'emerald', dot: 'bg-emerald-500', header: 'bg-emerald-50 border-emerald-200' },
  { type: 'job.completed', label: 'Completed', color: 'slate', dot: 'bg-slate-400', header: 'bg-slate-50 border-slate-200' },
]

const ISSUE_ICONS: Record<IssueType, ComponentType<{ className?: string }>> = {
  AC: Snowflake,
  Heating: Thermometer,
  Maintenance: Wrench,
  Emergency: Zap,
}

const ISSUE_COLORS: Record<IssueType, string> = {
  AC: 'text-blue-600 bg-blue-50',
  Heating: 'text-orange-600 bg-orange-50',
  Maintenance: 'text-emerald-600 bg-emerald-50',
  Emergency: 'text-red-600 bg-red-50',
}

const URGENCY_BADGE: Record<string, string> = {
  emergency: 'bg-red-100 text-red-700 ring-1 ring-red-300',
  urgent: 'bg-orange-100 text-orange-700',
  standard: 'bg-blue-100 text-blue-700',
  low: 'bg-slate-100 text-slate-600',
}

function JobCard({ pheromone }: { pheromone: Pheromone }) {
  const payload = pheromone.payload as Partial<JobPayload>
  const issue = payload.issue as IssueType | undefined
  const urgency = payload.urgency || 'standard'
  const IssueIcon = issue ? ISSUE_ICONS[issue] : Wrench

  return (
    <div className={`bg-white rounded-lg border p-4 shadow-sm hover:shadow-md transition-shadow ${
      urgency === 'emergency' ? 'border-red-300 ring-1 ring-red-200' : 'border-slate-200'
    }`}>
      {/* Header row */}
      <div className="flex items-start justify-between gap-2 mb-3">
        <p className="font-semibold text-slate-800 text-sm leading-tight">{payload.customer}</p>
        <span className={`text-xs font-medium px-2 py-0.5 rounded-full flex-shrink-0 capitalize ${URGENCY_BADGE[urgency]}`}>
          {urgency}
        </span>
      </div>

      {/* Address */}
      <div className="flex items-center gap-1.5 text-xs text-slate-500 mb-2">
        <MapPin className="w-3 h-3 flex-shrink-0" />
        <span className="truncate">{payload.address}</span>
      </div>

      {/* Issue type */}
      {issue && (
        <div className={`inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full mb-3 ${ISSUE_COLORS[issue]}`}>
          <IssueIcon className="w-3 h-3" />
          {issue}
        </div>
      )}

      {/* Tech (if assigned) */}
      {payload.tech_name && (
        <div className="flex items-center gap-1.5 text-xs text-slate-600 mb-2">
          <User className="w-3 h-3 text-slate-400" />
          {payload.tech_name}
        </div>
      )}

      {/* Time */}
      <div className="flex items-center gap-1 text-xs text-slate-400 mt-2 pt-2 border-t border-slate-100">
        <Clock className="w-3 h-3" />
        {formatDistanceToNow(new Date(pheromone.deposited_at), { addSuffix: true })}
      </div>
    </div>
  )
}

function BoardView() {
  const { pheromones } = useDashboardStore()

  const jobsByColumn = useMemo(() => {
    const map: Record<string, Pheromone[]> = {}
    COLUMNS.forEach(col => {
      map[col.type] = pheromones.filter(p => p.type === col.type)
    })
    return map
  }, [pheromones])

  const totalJobs = useMemo(
    () => Object.values(jobsByColumn).reduce((sum, jobs) => sum + jobs.length, 0),
    [jobsByColumn]
  )

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Job Board</h1>
          <p className="text-slate-500 mt-0.5">{totalJobs} active jobs</p>
        </div>
        <div className="flex gap-2">
          {COLUMNS.map(col => {
            const count = jobsByColumn[col.type]?.length || 0
            return (
              <div key={col.type} className="text-center">
                <div className={`text-xs font-medium px-2 py-1 rounded ${col.header} border`}>
                  <span className="text-slate-600">{col.label}</span>
                  <span className="ml-1.5 font-bold text-slate-800">{count}</span>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Kanban */}
      <div className="flex gap-4 overflow-x-auto pb-4">
        {COLUMNS.map(col => {
          const jobs = jobsByColumn[col.type] || []
          return (
            <div key={col.type} className="flex-shrink-0 w-72">
              {/* Column Header */}
              <div className={`flex items-center gap-2 px-3 py-2.5 rounded-t-xl border ${col.header} mb-2`}>
                <div className={`w-2.5 h-2.5 rounded-full ${col.dot}`} />
                <span className="text-sm font-semibold text-slate-700">{col.label}</span>
                <span className="ml-auto text-xs font-bold text-slate-500 bg-white rounded-full px-2 py-0.5 border border-slate-200">
                  {jobs.length}
                </span>
              </div>

              {/* Cards */}
              <div className="space-y-3 min-h-[200px]">
                {jobs.length === 0 ? (
                  <div className="border-2 border-dashed border-slate-200 rounded-lg p-6 text-center">
                    <p className="text-xs text-slate-400">No jobs</p>
                  </div>
                ) : (
                  jobs.map(p => <JobCard key={p.id} pheromone={p} />)
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default BoardView

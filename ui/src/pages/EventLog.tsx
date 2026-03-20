import { useState, useMemo } from 'react'
import { useDashboardStore } from '../store'
import {
  Search,
  Filter,
  ArrowDown,
  ArrowUp,
  Clock,
  Snowflake,
  Thermometer,
  Wrench,
  Zap,
  CheckCircle,
  ChevronDown,
  ChevronUp,
} from 'lucide-react'
import { format, formatDistanceToNow } from 'date-fns'
import type { BoardEvent } from '../types'
import type { JobPayload, IssueType } from '../types'
import type { ComponentType } from 'react'

const ISSUE_ICONS: Record<IssueType, ComponentType<{ className?: string }>> = {
  AC: Snowflake,
  Heating: Thermometer,
  Maintenance: Wrench,
  Emergency: Zap,
}

function describeEvent(event: BoardEvent): { title: string; detail: string } {
  const p = event.pheromone
  if (event.event_type === 'evaporated') {
    return { title: 'Signal evaporated', detail: event.pheromone_id.slice(0, 8) }
  }
  if (!p) return { title: 'Unknown event', detail: '' }
  const payload = p.payload as Partial<JobPayload>
  const customer = payload.customer || 'Unknown customer'
  const address = payload.address || ''
  const tech = payload.tech_name || ''

  switch (p.type) {
    case 'job.requested':
      return {
        title: `New service request from ${customer}`,
        detail: `${payload.issue} issue · ${payload.urgency} urgency · ${address}`,
      }
    case 'job.qualified':
      return {
        title: `Lead qualified: ${customer}`,
        detail: `${payload.issue} at ${address} — ready for dispatch`,
      }
    case 'job.dispatched':
      return {
        title: `${tech} dispatched to ${customer}`,
        detail: `${payload.issue} job at ${address}`,
      }
    case 'job.on_site':
      return {
        title: `${tech} arrived on-site`,
        detail: `Working on ${payload.issue} for ${customer} at ${address}`,
      }
    case 'job.completed':
      return {
        title: `Job completed for ${customer}`,
        detail: `${payload.issue} service at ${address}${tech ? ` · Tech: ${tech}` : ''}`,
      }
    case 'invoice.ready':
      return {
        title: `Invoice generated for ${customer}`,
        detail: address,
      }
    case 'followup.sent':
      return {
        title: `Follow-up sent to ${customer}`,
        detail: '',
      }
    default:
      return {
        title: p.type,
        detail: JSON.stringify(p.payload).slice(0, 80),
      }
  }
}

function typeIcon(event: BoardEvent) {
  const p = event.pheromone
  if (!p) return null
  const payload = p.payload as Partial<JobPayload>
  const issue = payload.issue as IssueType | undefined
  if (issue && ISSUE_ICONS[issue]) {
    const Icon = ISSUE_ICONS[issue]
    return <Icon className="w-4 h-4 flex-shrink-0" />
  }
  return <CheckCircle className="w-4 h-4 flex-shrink-0 text-blue-500" />
}

function iconBg(event: BoardEvent) {
  const p = event.pheromone
  if (!p || event.event_type === 'evaporated') return 'bg-slate-100 text-slate-400'
  const payload = p.payload as Partial<JobPayload>
  const issue = payload.issue as IssueType | undefined
  switch (issue) {
    case 'AC': return 'bg-blue-100 text-blue-600'
    case 'Heating': return 'bg-orange-100 text-orange-600'
    case 'Maintenance': return 'bg-emerald-100 text-emerald-600'
    case 'Emergency': return 'bg-red-100 text-red-600'
    default: return 'bg-blue-100 text-blue-600'
  }
}

function ActivityRow({ event }: { event: BoardEvent }) {
  const [expanded, setExpanded] = useState(false)
  const { title, detail } = describeEvent(event)

  return (
    <div className="border-b border-slate-100 last:border-0">
      <div
        className="flex items-center gap-4 px-5 py-3.5 cursor-pointer hover:bg-slate-50/80 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        {/* Icon */}
        <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${iconBg(event)}`}>
          {typeIcon(event)}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-slate-800 truncate">{title}</p>
          {detail && <p className="text-xs text-slate-500 mt-0.5 truncate">{detail}</p>}
        </div>

        {/* Time */}
        <div className="text-right flex-shrink-0">
          <p className="text-xs text-slate-500">
            {formatDistanceToNow(new Date(event.timestamp), { addSuffix: true })}
          </p>
          <p className="text-xs text-slate-400 mt-0.5">
            {format(new Date(event.timestamp), 'HH:mm:ss')}
          </p>
        </div>

        {/* Expand */}
        {expanded ? (
          <ChevronUp className="w-4 h-4 text-slate-400 flex-shrink-0" />
        ) : (
          <ChevronDown className="w-4 h-4 text-slate-400 flex-shrink-0" />
        )}
      </div>

      {/* Expanded payload */}
      {expanded && event.pheromone && (
        <div className="px-5 pb-4 ml-12">
          <div className="bg-slate-50 rounded-lg p-4 border border-slate-200">
            <div className="grid grid-cols-2 gap-x-8 gap-y-2 text-xs mb-3">
              <div>
                <span className="text-slate-400">Signal type</span>
                <span className="ml-2 font-mono text-slate-700">{event.pheromone.type}</span>
              </div>
              <div>
                <span className="text-slate-400">Deposited by</span>
                <span className="ml-2 text-slate-700">{event.pheromone.deposited_by}</span>
              </div>
              <div>
                <span className="text-slate-400">Trail ID</span>
                <span className="ml-2 font-mono text-slate-600">
                  {event.pheromone.trail_id?.slice(0, 12) || '—'}
                </span>
              </div>
              <div>
                <span className="text-slate-400">Intensity</span>
                <span className="ml-2 text-slate-700">{event.pheromone.intensity.toFixed(2)}</span>
              </div>
            </div>
            <p className="text-xs text-slate-400 mb-1">Payload</p>
            <pre className="text-xs bg-white rounded p-3 border border-slate-200 overflow-x-auto text-slate-700">
              {JSON.stringify(event.pheromone.payload, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  )
}

function EventLog() {
  const { events } = useDashboardStore()
  const [search, setSearch] = useState('')
  const [sortDesc, setSortDesc] = useState(true)

  const filtered = useMemo(() => {
    let result = [...events]
    if (search) {
      const q = search.toLowerCase()
      result = result.filter(e => {
        const p = e.pheromone
        if (!p) return false
        const payload = p.payload as Partial<JobPayload>
        return (
          p.type.toLowerCase().includes(q) ||
          (payload.customer || '').toLowerCase().includes(q) ||
          (payload.address || '').toLowerCase().includes(q) ||
          (payload.tech_name || '').toLowerCase().includes(q) ||
          (payload.issue || '').toLowerCase().includes(q)
        )
      })
    }
    result.sort((a, b) => {
      const diff = new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
      return sortDesc ? diff : -diff
    })
    return result
  }, [events, search, sortDesc])

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Activity Feed</h1>
        <p className="text-slate-500 mt-0.5">Complete history of HVAC operations</p>
      </div>

      {/* Controls */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[220px] max-w-sm">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search customer, tech, address..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        <button
          onClick={() => setSortDesc(!sortDesc)}
          className="flex items-center gap-2 px-3 py-2 border border-slate-200 rounded-lg hover:bg-slate-50 text-sm text-slate-600"
        >
          {sortDesc ? <ArrowDown className="w-4 h-4" /> : <ArrowUp className="w-4 h-4" />}
          {sortDesc ? 'Newest first' : 'Oldest first'}
        </button>

        <div className="flex items-center gap-2 text-sm text-slate-500">
          <Filter className="w-4 h-4" />
          <span>{filtered.length} events</span>
          {search && <span className="text-slate-400">of {events.length}</span>}
        </div>
      </div>

      {/* List */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        {filtered.length === 0 ? (
          <div className="p-12 text-center">
            <Clock className="w-10 h-10 text-slate-300 mx-auto mb-3" />
            <p className="text-slate-500">
              {search ? 'No matching activity' : 'No activity yet'}
            </p>
          </div>
        ) : (
          <div className="max-h-[600px] overflow-y-auto divide-y divide-slate-100">
            {filtered.map(event => (
              <ActivityRow key={event.id} event={event} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default EventLog

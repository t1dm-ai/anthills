import { useMemo } from 'react'
import { useDashboardStore } from '../store'
import {
  Snowflake,
  Thermometer,
  Wrench,
  Zap,
  Users,
  CheckCircle,
  Clock,
  AlertTriangle,
  Bot,
  Loader2,
  Pause,
  XCircle,
  MapPin,
} from 'lucide-react'
import { formatDistanceToNow, format } from 'date-fns'
import type { ComponentType } from 'react'
import type { JobPayload } from '../types'

interface StatCardProps {
  title: string
  value: string | number
  icon: ComponentType<{ className?: string }>
  color: string
  sub?: string
}

function StatCard({ title, value, icon: Icon, color, sub }: StatCardProps) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-slate-500">{title}</p>
          <p className="text-3xl font-bold text-slate-800 mt-1">{value}</p>
          {sub && <p className="text-xs text-slate-400 mt-1">{sub}</p>}
        </div>
        <div className={`p-3 rounded-xl ${color}`}>
          <Icon className="w-5 h-5 text-white" />
        </div>
      </div>
    </div>
  )
}

function Dashboard() {
  const { pheromones, workers, technicians, colony, events } = useDashboardStore()

  const jobs = useMemo(
    () => pheromones.filter(p => p.type.startsWith('job.')),
    [pheromones]
  )

  const openJobs = jobs.filter(p =>
    ['job.requested', 'job.qualified', 'job.dispatched'].includes(p.type)
  )
  const onSiteJobs = jobs.filter(p => p.type === 'job.on_site')
  const completedToday = jobs.filter(p => p.type === 'job.completed')
  const emergencies = jobs.filter(p => {
    const payload = p.payload as Partial<JobPayload>
    return payload.urgency === 'emergency' && p.type !== 'job.completed'
  })

  const issueBreakdown = useMemo(() => {
    const counts: Record<string, number> = { AC: 0, Heating: 0, Maintenance: 0, Emergency: 0 }
    jobs.forEach(p => {
      const payload = p.payload as Partial<JobPayload>
      if (payload.issue && payload.issue in counts) {
        counts[payload.issue]++
      }
    })
    const total = Object.values(counts).reduce((a, b) => a + b, 0) || 1
    return Object.entries(counts).map(([label, count]) => ({
      label,
      count,
      pct: Math.round((count / total) * 100),
    }))
  }, [jobs])

  const issueIcons: Record<string, ComponentType<{ className?: string }>> = {
    AC: Snowflake,
    Heating: Thermometer,
    Maintenance: Wrench,
    Emergency: Zap,
  }

  const issueColors: Record<string, string> = {
    AC: 'text-blue-600 bg-blue-50',
    Heating: 'text-orange-600 bg-orange-50',
    Maintenance: 'text-emerald-600 bg-emerald-50',
    Emergency: 'text-red-600 bg-red-50',
  }

  const barColors: Record<string, string> = {
    AC: 'bg-blue-500',
    Heating: 'bg-orange-500',
    Maintenance: 'bg-emerald-500',
    Emergency: 'bg-red-500',
  }

  const recentActivity = events.slice(0, 6)

  function describeEvent(event: typeof events[number]) {
    const p = event.pheromone
    if (!p) return 'Signal evaporated'
    const payload = p.payload as Partial<JobPayload>
    const customer = payload.customer || 'Unknown'
    const tech = payload.tech_name || ''
    switch (p.type) {
      case 'job.requested': return `New request from ${customer}`
      case 'job.qualified': return `Lead qualified: ${customer}`
      case 'job.dispatched': return `${tech} dispatched to ${customer}`
      case 'job.on_site': return `${tech} on-site at ${customer}`
      case 'job.completed': return `Job completed for ${customer}`
      case 'invoice.ready': return `Invoice ready for ${customer}`
      default: return p.type
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Operations Center</h1>
          <p className="text-slate-500 mt-0.5">{format(new Date(), 'EEEE, MMMM d, yyyy')}</p>
        </div>
        {colony?.started_at && (
          <div className="text-right">
            <p className="text-xs text-slate-400">Shift started</p>
            <p className="text-sm font-medium text-slate-600">
              {format(new Date(colony.started_at), 'h:mm a')}
            </p>
          </div>
        )}
      </div>

      {/* Emergency Alert */}
      {emergencies.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold text-red-800">
              {emergencies.length} Emergency {emergencies.length === 1 ? 'Job' : 'Jobs'} Active
            </p>
            <div className="mt-1 space-y-1">
              {emergencies.map(p => {
                const payload = p.payload as Partial<JobPayload>
                return (
                  <p key={p.id} className="text-sm text-red-700 flex items-center gap-1.5">
                    <MapPin className="w-3 h-3" />
                    {payload.customer} — {payload.address}
                    {payload.tech_name && (
                      <span className="text-red-500"> · {payload.tech_name} on site</span>
                    )}
                  </p>
                )
              })}
            </div>
          </div>
        </div>
      )}

      {/* Stat Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Open Jobs"
          value={openJobs.length}
          icon={Clock}
          color="bg-blue-500"
          sub="Pending attention"
        />
        <StatCard
          title="Techs On-Site"
          value={onSiteJobs.length}
          icon={Users}
          color="bg-emerald-500"
          sub={`of ${technicians.length} total`}
        />
        <StatCard
          title="Completed Today"
          value={completedToday.length}
          icon={CheckCircle}
          color="bg-purple-500"
          sub="Great work!"
        />
        <StatCard
          title="Active Agents"
          value={workers.filter(w => w.status === 'busy').length}
          icon={Bot}
          color="bg-amber-500"
          sub={`of ${workers.length} running`}
        />
      </div>

      {/* Two-Column */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Issue Breakdown */}
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <h2 className="text-base font-semibold text-slate-800 mb-4">Jobs by Issue Type</h2>
          <div className="space-y-3">
            {issueBreakdown.map(({ label, count, pct }) => {
              const Icon = issueIcons[label]
              return (
                <div key={label}>
                  <div className="flex items-center justify-between mb-1">
                    <div className={`flex items-center gap-2 text-sm font-medium ${issueColors[label].split(' ')[0]}`}>
                      <span className={`p-1 rounded ${issueColors[label]}`}>
                        <Icon className="w-3.5 h-3.5" />
                      </span>
                      {label}
                    </div>
                    <span className="text-sm font-semibold text-slate-700">{count}</span>
                  </div>
                  <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className={`h-full ${barColors[label]} transition-all`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Technician Status */}
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <h2 className="text-base font-semibold text-slate-800 mb-4">Technician Status</h2>
          <div className="space-y-3">
            {technicians.map(tech => (
              <div key={tech.id} className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${
                    tech.status === 'on_site'
                      ? 'bg-emerald-100 text-emerald-700'
                      : tech.status === 'en_route'
                      ? 'bg-blue-100 text-blue-700'
                      : 'bg-slate-100 text-slate-600'
                  }`}>
                    {tech.name.split(' ').map(n => n[0]).join('')}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-800">{tech.name}</p>
                    <p className="text-xs text-slate-500">{tech.region}</p>
                  </div>
                </div>
                <div className="text-right">
                  <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                    tech.status === 'on_site'
                      ? 'bg-emerald-100 text-emerald-700'
                      : tech.status === 'en_route'
                      ? 'bg-blue-100 text-blue-700'
                      : 'bg-slate-100 text-slate-600'
                  }`}>
                    {tech.status === 'en_route' ? 'En Route' : tech.status === 'on_site' ? 'On Site' : 'Available'}
                  </span>
                  <p className="text-xs text-slate-400 mt-0.5">{tech.jobs_today} jobs today</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* AI Agents + Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* AI Agents */}
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <h2 className="text-base font-semibold text-slate-800 mb-4">AI Agents</h2>
          <div className="space-y-3">
            {workers.map(w => (
              <div key={w.id} className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                    w.status === 'busy' ? 'bg-amber-100' : 'bg-slate-100'
                  }`}>
                    {w.status === 'busy' ? (
                      <Loader2 className="w-4 h-4 text-amber-600 animate-spin" />
                    ) : w.status === 'error' ? (
                      <XCircle className="w-4 h-4 text-red-500" />
                    ) : (
                      <Pause className="w-4 h-4 text-slate-500" />
                    )}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-800">{w.name}</p>
                    <p className="text-xs font-mono text-slate-400">{w.reacts_to}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-semibold text-slate-700">{w.processed_count}</p>
                  <p className="text-xs text-slate-400">processed</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <h2 className="text-base font-semibold text-slate-800 mb-4">Recent Activity</h2>
          <div className="space-y-3">
            {recentActivity.length === 0 ? (
              <p className="text-sm text-slate-500">No activity yet</p>
            ) : (
              recentActivity.map(event => (
                <div key={event.id} className="flex items-start gap-3 text-sm">
                  <div className={`w-2 h-2 rounded-full mt-1.5 flex-shrink-0 ${
                    event.event_type === 'deposit' ? 'bg-blue-500' : 'bg-slate-300'
                  }`} />
                  <div className="flex-1 min-w-0">
                    <p className="text-slate-700 truncate">{describeEvent(event)}</p>
                    <p className="text-xs text-slate-400">
                      {formatDistanceToNow(new Date(event.timestamp), { addSuffix: true })}
                    </p>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default Dashboard

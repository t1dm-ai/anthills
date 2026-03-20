import { useDashboardStore } from '../store'
import {
  MapPin,
  Phone,
  CheckCircle,
  Truck,
  CircleDot,
  Shield,
  Bot,
  Loader2,
  Pause,
  XCircle,
  Tag,
  Clock,
} from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import type { Technician, Worker } from '../types'

function TechCard({ tech }: { tech: Technician }) {
  const statusConfig = {
    available: {
      label: 'Available',
      badge: 'bg-green-100 text-green-700',
      icon: CircleDot,
      iconColor: 'text-green-500',
      bg: 'bg-green-50',
    },
    en_route: {
      label: 'En Route',
      badge: 'bg-blue-100 text-blue-700',
      icon: Truck,
      iconColor: 'text-blue-500',
      bg: 'bg-blue-50',
    },
    on_site: {
      label: 'On Site',
      badge: 'bg-emerald-100 text-emerald-700',
      icon: MapPin,
      iconColor: 'text-emerald-500',
      bg: 'bg-emerald-50',
    },
  }

  const cfg = statusConfig[tech.status]
  const StatusIcon = cfg.icon
  const initials = tech.name.split(' ').map(n => n[0]).join('')

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 hover:shadow-md transition-shadow">
      {/* Top row */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-full ${cfg.bg} flex items-center justify-center font-bold text-sm ${cfg.iconColor}`}>
            {initials}
          </div>
          <div>
            <p className="font-semibold text-slate-800">{tech.name}</p>
            <div className="flex items-center gap-1 text-xs text-slate-500 mt-0.5">
              <MapPin className="w-3 h-3" />
              {tech.region}
            </div>
          </div>
        </div>
        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${cfg.badge}`}>
          <StatusIcon className="w-3 h-3" />
          {cfg.label}
        </span>
      </div>

      {/* Phone */}
      <div className="flex items-center gap-2 text-xs text-slate-500 mb-3">
        <Phone className="w-3.5 h-3.5" />
        {tech.phone}
      </div>

      {/* Certifications */}
      <div className="flex flex-wrap gap-1.5 mb-4">
        {tech.certifications.map(cert => (
          <span
            key={cert}
            className="inline-flex items-center gap-1 px-2 py-0.5 bg-slate-100 text-slate-600 rounded text-xs font-medium"
          >
            <Shield className="w-3 h-3" />
            {cert}
          </span>
        ))}
      </div>

      {/* Footer stats */}
      <div className="flex items-center justify-between pt-3 border-t border-slate-100">
        <div className="flex items-center gap-1 text-sm">
          <CheckCircle className="w-4 h-4 text-green-500" />
          <span className="font-semibold text-slate-800">{tech.jobs_today}</span>
          <span className="text-slate-500 text-xs">jobs today</span>
        </div>
        {tech.current_job_id && (
          <span className="text-xs text-blue-600 font-medium bg-blue-50 px-2 py-0.5 rounded-full">
            Active job
          </span>
        )}
      </div>
    </div>
  )
}

function AgentCard({ worker }: { worker: Worker }) {
  const statusCfg = {
    idle: { badge: 'bg-slate-100 text-slate-600', icon: Pause, spin: false },
    busy: { badge: 'bg-amber-100 text-amber-700', icon: Loader2, spin: true },
    error: { badge: 'bg-red-100 text-red-700', icon: XCircle, spin: false },
  }

  const cfg = statusCfg[worker.status]
  const StatusIcon = cfg.icon

  const agentDescriptions: Record<string, string> = {
    LeadQualifier: 'Evaluates new service requests and qualifies leads',
    Dispatcher: 'Assigns qualified jobs to available technicians',
    InvoiceProcessor: 'Generates invoices when jobs are completed',
    FollowupAgent: 'Sends customer follow-ups after payment',
  }

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
            worker.status === 'busy' ? 'bg-amber-50' : 'bg-slate-100'
          }`}>
            <Bot className={`w-5 h-5 ${worker.status === 'busy' ? 'text-amber-600' : 'text-slate-500'}`} />
          </div>
          <div>
            <p className="font-semibold text-slate-800">{worker.name}</p>
            <span className={`inline-flex items-center gap-1 text-xs font-medium px-1.5 py-0.5 rounded ${cfg.badge}`}>
              <StatusIcon className={`w-2.5 h-2.5 ${cfg.spin ? 'animate-spin' : ''}`} />
              {worker.status}
            </span>
          </div>
        </div>
      </div>

      <p className="text-xs text-slate-500 mb-3 leading-relaxed">
        {agentDescriptions[worker.name] || 'AI agent'}
      </p>

      {/* Reacts to */}
      <div className="flex items-center gap-1.5 text-xs text-slate-500 mb-4">
        <Tag className="w-3 h-3" />
        <span className="font-mono bg-slate-100 px-1.5 py-0.5 rounded text-slate-600">
          {worker.reacts_to}
        </span>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-3 pt-3 border-t border-slate-100">
        <div>
          <p className="text-xs text-slate-400">Processed</p>
          <p className="text-lg font-bold text-slate-800">{worker.processed_count}</p>
        </div>
        <div>
          <p className="text-xs text-slate-400">Errors</p>
          <p className="text-lg font-bold text-red-600">{worker.error_count}</p>
        </div>
        <div>
          <p className="text-xs text-slate-400">Last Active</p>
          <p className="text-xs text-slate-600 mt-1 flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {worker.last_active
              ? formatDistanceToNow(new Date(worker.last_active), { addSuffix: true })
              : 'Never'}
          </p>
        </div>
      </div>
    </div>
  )
}

function WorkersView() {
  const { technicians, workers } = useDashboardStore()

  const availableTechs = technicians.filter(t => t.status === 'available').length
  const onSiteTechs = technicians.filter(t => t.status === 'on_site').length
  const enRouteTechs = technicians.filter(t => t.status === 'en_route').length

  return (
    <div className="space-y-8">
      {/* Technicians Section */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-800">Field Team</h1>
            <p className="text-slate-500 mt-0.5">
              {onSiteTechs} on-site · {enRouteTechs} en route · {availableTechs} available
            </p>
          </div>
        </div>

        {/* Tech summary bar */}
        <div className="flex gap-3 mb-5">
          {[
            { label: 'Available', count: availableTechs, color: 'bg-green-100 text-green-700 border-green-200' },
            { label: 'En Route', count: enRouteTechs, color: 'bg-blue-100 text-blue-700 border-blue-200' },
            { label: 'On Site', count: onSiteTechs, color: 'bg-emerald-100 text-emerald-700 border-emerald-200' },
          ].map(({ label, count, color }) => (
            <div key={label} className={`px-4 py-2 rounded-lg border text-sm font-medium ${color}`}>
              {count} {label}
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {technicians.map(tech => (
            <TechCard key={tech.id} tech={tech} />
          ))}
        </div>
      </div>

      {/* AI Agents Section */}
      <div>
        <div className="mb-4">
          <h2 className="text-xl font-bold text-slate-800">AI Agents</h2>
          <p className="text-slate-500 mt-0.5">
            Powered by Claude · {workers.filter(w => w.status === 'busy').length} currently processing
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {workers.map(worker => (
            <AgentCard key={worker.id} worker={worker} />
          ))}
        </div>
      </div>
    </div>
  )
}

export default WorkersView

import { useState, useMemo } from 'react'
import { useDashboardStore } from '../store'
import {
  Snowflake,
  Thermometer,
  Wrench,
  Zap,
  MapPin,
  User,
  Phone,
  Clock,
  Send,
  CheckCircle,
} from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import type { IssueType, Urgency, JobPayload } from '../types'

const ISSUE_OPTIONS: { value: IssueType; label: string; icon: typeof Snowflake; color: string }[] = [
  { value: 'AC', label: 'Air Conditioning', icon: Snowflake, color: 'border-blue-300 bg-blue-50 text-blue-700' },
  { value: 'Heating', label: 'Heating', icon: Thermometer, color: 'border-orange-300 bg-orange-50 text-orange-700' },
  { value: 'Maintenance', label: 'Maintenance', icon: Wrench, color: 'border-emerald-300 bg-emerald-50 text-emerald-700' },
  { value: 'Emergency', label: 'Emergency', icon: Zap, color: 'border-red-300 bg-red-50 text-red-700' },
]

const URGENCY_OPTIONS: { value: Urgency; label: string; description: string }[] = [
  { value: 'low', label: 'Low', description: 'Within a week' },
  { value: 'standard', label: 'Standard', description: '1-2 business days' },
  { value: 'urgent', label: 'Urgent', description: 'Today or tomorrow' },
  { value: 'emergency', label: 'Emergency', description: 'Within hours' },
]

const URGENCY_BADGE: Record<Urgency, string> = {
  low: 'bg-slate-100 text-slate-600',
  standard: 'bg-blue-100 text-blue-700',
  urgent: 'bg-orange-100 text-orange-700',
  emergency: 'bg-red-100 text-red-700',
}

const ISSUE_ICONS: Record<IssueType, typeof Snowflake> = {
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

const defaultForm = {
  customer: '',
  phone: '',
  address: '',
  issue: 'AC' as IssueType,
  urgency: 'standard' as Urgency,
  notes: '',
}

function ServiceRequests() {
  const { pheromones, addServiceRequest } = useDashboardStore()
  const [form, setForm] = useState(defaultForm)
  const [submitted, setSubmitted] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})

  const pendingRequests = useMemo(
    () => pheromones
      .filter(p => p.type === 'job.requested')
      .sort((a, b) => new Date(b.deposited_at).getTime() - new Date(a.deposited_at).getTime()),
    [pheromones]
  )

  function validate() {
    const errs: Record<string, string> = {}
    if (!form.customer.trim()) errs.customer = 'Customer name is required'
    if (!form.phone.trim()) errs.phone = 'Phone number is required'
    if (!form.address.trim()) errs.address = 'Address is required'
    return errs
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const errs = validate()
    if (Object.keys(errs).length) {
      setErrors(errs)
      return
    }
    const payload: JobPayload = {
      customer: form.customer.trim(),
      phone: form.phone.trim(),
      address: form.address.trim(),
      issue: form.issue,
      urgency: form.urgency,
      notes: form.notes.trim() || undefined,
    }
    addServiceRequest(payload)
    setForm(defaultForm)
    setErrors({})
    setSubmitted(true)
    setTimeout(() => setSubmitted(false), 3000)
  }

  return (
    <div className="space-y-6 max-w-5xl">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Service Requests</h1>
        <p className="text-slate-500 mt-0.5">Submit a new job request — it will be picked up by the AI qualifier</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Form */}
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <h2 className="text-base font-semibold text-slate-800 mb-5">New Request</h2>

          {submitted && (
            <div className="flex items-center gap-2 bg-green-50 border border-green-200 rounded-lg px-4 py-3 mb-5 text-green-700 text-sm">
              <CheckCircle className="w-4 h-4" />
              Request submitted! The LeadQualifier agent is on it.
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Customer Name */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">
                <User className="w-3.5 h-3.5 inline mr-1.5 text-slate-400" />
                Customer Name
              </label>
              <input
                type="text"
                value={form.customer}
                onChange={e => setForm({ ...form, customer: e.target.value })}
                placeholder="Jane Smith"
                className={`w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  errors.customer ? 'border-red-300' : 'border-slate-200'
                }`}
              />
              {errors.customer && <p className="text-xs text-red-500 mt-1">{errors.customer}</p>}
            </div>

            {/* Phone */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">
                <Phone className="w-3.5 h-3.5 inline mr-1.5 text-slate-400" />
                Phone Number
              </label>
              <input
                type="tel"
                value={form.phone}
                onChange={e => setForm({ ...form, phone: e.target.value })}
                placeholder="(555) 000-0000"
                className={`w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  errors.phone ? 'border-red-300' : 'border-slate-200'
                }`}
              />
              {errors.phone && <p className="text-xs text-red-500 mt-1">{errors.phone}</p>}
            </div>

            {/* Address */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">
                <MapPin className="w-3.5 h-3.5 inline mr-1.5 text-slate-400" />
                Service Address
              </label>
              <input
                type="text"
                value={form.address}
                onChange={e => setForm({ ...form, address: e.target.value })}
                placeholder="123 Main St, Springfield"
                className={`w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  errors.address ? 'border-red-300' : 'border-slate-200'
                }`}
              />
              {errors.address && <p className="text-xs text-red-500 mt-1">{errors.address}</p>}
            </div>

            {/* Issue Type */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Issue Type</label>
              <div className="grid grid-cols-2 gap-2">
                {ISSUE_OPTIONS.map(opt => {
                  const Icon = opt.icon
                  return (
                    <button
                      key={opt.value}
                      type="button"
                      onClick={() => setForm({ ...form, issue: opt.value })}
                      className={`flex items-center gap-2 px-3 py-2.5 rounded-lg border-2 text-sm font-medium transition-all ${
                        form.issue === opt.value
                          ? opt.color
                          : 'border-slate-200 text-slate-500 hover:border-slate-300'
                      }`}
                    >
                      <Icon className="w-4 h-4" />
                      {opt.label}
                    </button>
                  )
                })}
              </div>
            </div>

            {/* Urgency */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Urgency</label>
              <div className="grid grid-cols-2 gap-2">
                {URGENCY_OPTIONS.map(opt => (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => setForm({ ...form, urgency: opt.value })}
                    className={`px-3 py-2.5 rounded-lg border-2 text-left transition-all ${
                      form.urgency === opt.value
                        ? 'border-blue-400 bg-blue-50'
                        : 'border-slate-200 hover:border-slate-300'
                    }`}
                  >
                    <p className="text-sm font-medium text-slate-800">{opt.label}</p>
                    <p className="text-xs text-slate-500 mt-0.5">{opt.description}</p>
                  </button>
                ))}
              </div>
            </div>

            {/* Notes */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">
                Notes <span className="text-slate-400 font-normal">(optional)</span>
              </label>
              <textarea
                value={form.notes}
                onChange={e => setForm({ ...form, notes: e.target.value })}
                placeholder="Describe the issue in more detail..."
                rows={3}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              />
            </div>

            <button
              type="submit"
              className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2.5 px-4 rounded-lg transition-colors"
            >
              <Send className="w-4 h-4" />
              Submit Request
            </button>
          </form>
        </div>

        {/* Pending Requests */}
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <h2 className="text-base font-semibold text-slate-800 mb-4">
            Pending Requests
            <span className="ml-2 text-sm font-normal text-slate-400">({pendingRequests.length})</span>
          </h2>

          {pendingRequests.length === 0 ? (
            <div className="text-center py-10">
              <CheckCircle className="w-10 h-10 text-slate-200 mx-auto mb-3" />
              <p className="text-slate-500 text-sm">No pending requests</p>
            </div>
          ) : (
            <div className="space-y-3 max-h-[500px] overflow-y-auto">
              {pendingRequests.map(p => {
                const payload = p.payload as Partial<JobPayload>
                const issue = payload.issue as IssueType | undefined
                const IssueIcon = issue ? ISSUE_ICONS[issue] : Wrench
                return (
                  <div
                    key={p.id}
                    className={`border rounded-lg p-4 ${
                      payload.urgency === 'emergency' ? 'border-red-200 bg-red-50' : 'border-slate-200'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <p className="font-medium text-slate-800 text-sm">{payload.customer}</p>
                      <span className={`text-xs font-medium px-2 py-0.5 rounded-full capitalize flex-shrink-0 ${
                        URGENCY_BADGE[payload.urgency as Urgency || 'standard']
                      }`}>
                        {payload.urgency}
                      </span>
                    </div>
                    <div className="flex items-center gap-1.5 text-xs text-slate-500 mb-2">
                      <MapPin className="w-3 h-3" />
                      {payload.address}
                    </div>
                    {issue && (
                      <div className={`inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full ${ISSUE_COLORS[issue]}`}>
                        <IssueIcon className="w-3 h-3" />
                        {issue}
                      </div>
                    )}
                    {payload.notes && (
                      <p className="text-xs text-slate-500 mt-2 line-clamp-2">{payload.notes}</p>
                    )}
                    <div className="flex items-center gap-1 text-xs text-slate-400 mt-2">
                      <Clock className="w-3 h-3" />
                      {formatDistanceToNow(new Date(p.deposited_at), { addSuffix: true })}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default ServiceRequests

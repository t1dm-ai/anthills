import { useState } from 'react'
import { useDashboardStore } from '../store'
import type { LedgerEntry } from '../types'

// ─── Helpers ──────────────────────────────────────────────────────────────────

const STATUS_COLORS: Record<string, string> = {
  running:   'bg-yellow-500/20 text-yellow-300 border border-yellow-500/30',
  completed: 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30',
  error:     'bg-red-500/20 text-red-300 border border-red-500/30',
}

const WORKER_COLORS: Record<string, string> = {
  LeadQualifier:    'text-violet-400',
  Dispatcher:       'text-blue-400',
  TechSimulator:    'text-cyan-400',
  JobCompleter:     'text-orange-400',
  InvoiceProcessor: 'text-emerald-400',
}

function shortHash(h: string | null) {
  return h ? h.slice(0, 8) + '…' : '—'
}

function formatDuration(ms: number | null) {
  if (ms === null) return '…'
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(1)}s`
}

function formatTime(iso: string) {
  return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function JsonBlock({ data, label }: { data: unknown; label: string }) {
  return (
    <div>
      <div className="text-xs text-slate-500 mb-1 font-mono uppercase tracking-wide">{label}</div>
      <pre className="text-xs bg-slate-950 rounded p-3 overflow-x-auto text-slate-300 border border-slate-800 leading-relaxed">
        {JSON.stringify(data, null, 2)}
      </pre>
    </div>
  )
}

function MessagesBlock({ messages }: { messages: Array<{ role: string; content: string }> }) {
  return (
    <div>
      <div className="text-xs text-slate-500 mb-2 font-mono uppercase tracking-wide">Messages sent to Claude</div>
      <div className="space-y-2">
        {messages.map((m, i) => (
          <div key={i} className={`rounded p-3 text-xs border ${m.role === 'user' ? 'bg-blue-950/40 border-blue-800/30 text-blue-200' : 'bg-slate-900 border-slate-700 text-slate-300'}`}>
            <div className="font-semibold uppercase text-[10px] tracking-wider mb-1 opacity-60">{m.role}</div>
            <pre className="whitespace-pre-wrap font-mono">{typeof m.content === 'string' ? m.content : JSON.stringify(m.content, null, 2)}</pre>
          </div>
        ))}
      </div>
    </div>
  )
}

function EntryDetail({ entry }: { entry: LedgerEntry }) {
  const isLLM = entry.model !== null

  return (
    <div className="mt-3 border-t border-slate-700/50 pt-4 space-y-4">
      {/* Input / Output side by side */}
      <div className="grid grid-cols-2 gap-4">
        <JsonBlock data={entry.input_payload} label="Input payload" />
        {entry.output_payload
          ? <JsonBlock data={entry.output_payload} label={`Output → ${entry.output_pheromone_type}`} />
          : entry.status === 'error'
          ? (
            <div>
              <div className="text-xs text-slate-500 mb-1 font-mono uppercase tracking-wide">Error</div>
              <div className="text-xs text-red-400 bg-red-950/40 rounded p-3 border border-red-800/30 font-mono">{entry.error}</div>
            </div>
          )
          : (
            <div className="flex items-center justify-center text-slate-600 text-xs">
              {entry.status === 'running' ? 'Awaiting output…' : 'No output deposited'}
            </div>
          )
        }
      </div>

      {/* LLM section */}
      {isLLM && (
        <div className="space-y-4 border-t border-violet-900/30 pt-4">
          <div className="flex items-center gap-2">
            <span className="text-[10px] uppercase tracking-wider text-violet-400 font-semibold">Claude call</span>
            <span className="text-[10px] text-slate-500">{entry.model}</span>
            {entry.token_usage && (
              <span className="text-[10px] text-slate-500 ml-auto">
                {entry.token_usage.input_tokens} in / {entry.token_usage.output_tokens} out tokens
              </span>
            )}
          </div>

          {entry.messages && <MessagesBlock messages={entry.messages as Array<{ role: string; content: string }>} />}

          {entry.thinking && entry.thinking.length > 0 && (
            <div>
              <div className="text-xs text-slate-500 mb-2 font-mono uppercase tracking-wide">Thinking</div>
              {entry.thinking.map((t, i) => (
                <pre key={i} className="text-xs bg-violet-950/30 rounded p-3 border border-violet-800/20 text-violet-200 whitespace-pre-wrap font-mono leading-relaxed">{t}</pre>
              ))}
            </div>
          )}

          {entry.raw_response_text && (
            <div>
              <div className="text-xs text-slate-500 mb-2 font-mono uppercase tracking-wide">Response</div>
              <pre className="text-xs bg-slate-950 rounded p-3 border border-slate-800 text-slate-300 whitespace-pre-wrap font-mono leading-relaxed">{entry.raw_response_text}</pre>
            </div>
          )}
        </div>
      )}

      {/* Chain proof */}
      <div className="border-t border-slate-800 pt-3">
        <div className="text-[10px] uppercase tracking-wider text-slate-500 mb-2 font-semibold">Chain proof</div>
        <div className="grid grid-cols-2 gap-2 text-[11px] font-mono">
          <div>
            <span className="text-slate-500">prev_hash </span>
            <span className="text-slate-400">{entry.prev_hash ? entry.prev_hash.slice(0, 16) + '…' : 'genesis'}</span>
          </div>
          <div>
            <span className="text-slate-500">hash </span>
            <span className={entry.hash ? 'text-emerald-400' : 'text-yellow-400'}>
              {entry.hash ? entry.hash.slice(0, 16) + '…' : 'unsealed'}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}

function EntryRow({ entry }: { entry: LedgerEntry }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div
      className={`rounded-lg border transition-all ${
        expanded ? 'border-slate-600 bg-slate-800/60' : 'border-slate-700/50 bg-slate-800/30 hover:border-slate-600/70'
      }`}
    >
      {/* Header row */}
      <button
        onClick={() => setExpanded(e => !e)}
        className="w-full text-left px-4 py-3 flex items-center gap-3"
      >
        {/* Status dot */}
        <div className={`w-2 h-2 rounded-full flex-shrink-0 ${
          entry.status === 'running'   ? 'bg-yellow-400 animate-pulse' :
          entry.status === 'completed' ? 'bg-emerald-400' : 'bg-red-400'
        }`} />

        {/* Worker name */}
        <span className={`text-sm font-semibold w-36 flex-shrink-0 ${WORKER_COLORS[entry.worker_name] ?? 'text-slate-300'}`}>
          {entry.worker_name}
        </span>

        {/* Trigger type */}
        <span className="text-xs text-slate-400 font-mono w-36 flex-shrink-0 truncate">
          {entry.trigger_pheromone_type}
        </span>

        {/* Arrow + output */}
        {entry.output_pheromone_type && (
          <>
            <span className="text-slate-600 text-xs">→</span>
            <span className="text-xs text-slate-300 font-mono truncate flex-1">{entry.output_pheromone_type}</span>
          </>
        )}
        {!entry.output_pheromone_type && <span className="flex-1" />}

        {/* Duration */}
        <span className="text-xs text-slate-500 w-12 text-right flex-shrink-0">
          {formatDuration(entry.duration_ms)}
        </span>

        {/* Status badge */}
        <span className={`text-[10px] px-2 py-0.5 rounded-full font-semibold flex-shrink-0 ${STATUS_COLORS[entry.status]}`}>
          {entry.status}
        </span>

        {/* Hash */}
        <span className="text-[10px] font-mono text-slate-600 w-20 text-right flex-shrink-0">
          {shortHash(entry.hash)}
        </span>

        {/* Time */}
        <span className="text-[10px] text-slate-600 w-16 text-right flex-shrink-0">
          {formatTime(entry.started_at)}
        </span>

        {/* Expand chevron */}
        <span className={`text-slate-500 text-xs transition-transform flex-shrink-0 ${expanded ? 'rotate-90' : ''}`}>▶</span>
      </button>

      {expanded && (
        <div className="px-4 pb-4">
          <EntryDetail entry={entry} />
        </div>
      )}
    </div>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function LedgerView() {
  const { ledger, chainValid } = useDashboardStore()
  const [filter, setFilter] = useState<string>('all')

  const workers = Array.from(new Set(ledger.map(e => e.worker_name)))

  const filtered = filter === 'all'
    ? ledger
    : ledger.filter(e => e.worker_name === filter)

  const completed = ledger.filter(e => e.status === 'completed').length
  const errors    = ledger.filter(e => e.status === 'error').length
  const running   = ledger.filter(e => e.status === 'running').length

  const totalTokens = ledger.reduce((sum, e) => {
    if (!e.token_usage) return sum
    return sum + e.token_usage.input_tokens + e.token_usage.output_tokens
  }, 0)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Agent Ledger</h1>
          <p className="text-slate-400 text-sm mt-1">
            Every agent decision, input, output, and LLM call — tamper-evident chain
          </p>
        </div>
        <div className={`flex items-center gap-2 text-xs px-3 py-1.5 rounded-full border font-mono ${
          chainValid
            ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
            : 'bg-red-500/10 border-red-500/30 text-red-400'
        }`}>
          <span className={`w-1.5 h-1.5 rounded-full ${chainValid ? 'bg-emerald-400' : 'bg-red-400'}`} />
          {chainValid ? 'Chain valid' : 'Chain broken'}
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-5 gap-4">
        {[
          { label: 'Total entries', value: ledger.length, color: 'text-white' },
          { label: 'Completed', value: completed, color: 'text-emerald-400' },
          { label: 'Running', value: running, color: 'text-yellow-400' },
          { label: 'Errors', value: errors, color: 'text-red-400' },
          { label: 'Total tokens', value: totalTokens.toLocaleString(), color: 'text-violet-400' },
        ].map(s => (
          <div key={s.label} className="bg-slate-800/50 rounded-lg p-4 border border-slate-700/50">
            <div className={`text-2xl font-bold ${s.color}`}>{s.value}</div>
            <div className="text-xs text-slate-400 mt-1">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Filter tabs */}
      <div className="flex gap-2 flex-wrap">
        {['all', ...workers].map(w => (
          <button
            key={w}
            onClick={() => setFilter(w)}
            className={`px-3 py-1 rounded-full text-xs font-semibold transition-colors ${
              filter === w
                ? 'bg-blue-600 text-white'
                : 'bg-slate-800 text-slate-400 hover:text-white border border-slate-700'
            }`}
          >
            {w === 'all' ? 'All agents' : w}
          </button>
        ))}
      </div>

      {/* Entries */}
      <div className="space-y-2">
        {filtered.length === 0 ? (
          <div className="text-center py-16 text-slate-500">
            <div className="text-4xl mb-3">📋</div>
            <div className="text-sm">No ledger entries yet</div>
            <div className="text-xs mt-1">Submit a service request to start the pipeline</div>
          </div>
        ) : (
          filtered.map(entry => <EntryRow key={entry.id} entry={entry} />)
        )}
      </div>
    </div>
  )
}

import { useState, useMemo } from 'react'
import { useDashboardStore } from '../store'
import { Search, Filter, ArrowDown, ArrowUp, Clock, Zap } from 'lucide-react'
import { format } from 'date-fns'
import type { BoardEvent } from '../types'

function EventRow({ event, index }: { event: BoardEvent; index: number }) {
  const [expanded, setExpanded] = useState(false)
  
  const typeColors: Record<string, string> = {
    deposit: 'bg-emerald-100 text-emerald-700',
    evaporated: 'bg-orange-100 text-orange-700',
  }
  
  return (
    <div className={`
      border-b border-slate-100 last:border-0
      ${index % 2 === 0 ? 'bg-white' : 'bg-slate-50/50'}
    `}>
      <div 
        className="flex items-center gap-4 px-4 py-3 cursor-pointer hover:bg-slate-100/50"
        onClick={() => setExpanded(!expanded)}
      >
        {/* ID (truncated) */}
        <span className="text-xs font-mono text-slate-400 w-16 truncate">
          {event.id.slice(0, 8)}
        </span>
        
        {/* Type Badge */}
        <span className={`
          px-2 py-0.5 rounded text-xs font-medium w-24 text-center
          ${typeColors[event.event_type] || 'bg-slate-100 text-slate-600'}
        `}>
          {event.event_type}
        </span>
        
        {/* Pheromone Type */}
        <span className="font-mono text-sm text-slate-700 flex-1 truncate">
          {event.pheromone?.type || event.pheromone_id.slice(0, 8)}
        </span>
        
        {/* Deposited By */}
        <span className="text-sm text-slate-500 w-32 truncate">
          {event.pheromone?.deposited_by || '-'}
        </span>
        
        {/* Timestamp */}
        <span className="text-xs text-slate-400 w-32 flex items-center gap-1">
          <Clock className="w-3 h-3" />
          {format(new Date(event.timestamp), 'HH:mm:ss.SSS')}
        </span>
        
        {/* Expand Arrow */}
        {expanded ? (
          <ArrowUp className="w-4 h-4 text-slate-400" />
        ) : (
          <ArrowDown className="w-4 h-4 text-slate-400" />
        )}
      </div>
      
      {/* Expanded Details */}
      {expanded && event.pheromone && (
        <div className="px-4 pb-4 ml-16">
          <div className="bg-slate-100 rounded-lg p-4">
            <div className="grid grid-cols-2 gap-4 mb-3 text-sm">
              <div>
                <span className="text-slate-500">Full Timestamp:</span>
                <span className="ml-2 text-slate-700">
                  {format(new Date(event.timestamp), 'yyyy-MM-dd HH:mm:ss.SSS')}
                </span>
              </div>
              <div>
                <span className="text-slate-500">Type:</span>
                <span className="ml-2 font-mono text-slate-700">{event.pheromone.type}</span>
              </div>
              <div>
                <span className="text-slate-500">Intensity:</span>
                <span className="ml-2 text-slate-700">{event.pheromone.intensity.toFixed(2)}</span>
              </div>
              <div>
                <span className="text-slate-500">TTL:</span>
                <span className="ml-2 text-slate-700">
                  {event.pheromone.ttl_seconds !== null ? `${event.pheromone.ttl_seconds}s` : 'None'}
                </span>
              </div>
            </div>
            
            <div>
              <span className="text-sm text-slate-500">Payload:</span>
              <pre className="mt-1 text-xs bg-white rounded p-3 overflow-x-auto">
                {JSON.stringify(event.pheromone.payload, null, 2)}
              </pre>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function EventLog() {
  const { events } = useDashboardStore()
  const [search, setSearch] = useState('')
  const [typeFilter, setTypeFilter] = useState<string>('')
  const [sortDesc, setSortDesc] = useState(true)
  
  const eventTypes = useMemo(() => {
    return [...new Set(events.map(e => e.event_type))]
  }, [events])
  
  const filteredEvents = useMemo(() => {
    let result = [...events]
    
    // Filter by search
    if (search) {
      const lower = search.toLowerCase()
      result = result.filter(e => 
        e.pheromone?.type.toLowerCase().includes(lower) ||
        e.pheromone?.deposited_by.toLowerCase().includes(lower) ||
        e.event_type.toLowerCase().includes(lower) ||
        JSON.stringify(e.pheromone?.payload).toLowerCase().includes(lower)
      )
    }
    
    // Filter by type
    if (typeFilter) {
      result = result.filter(e => e.event_type === typeFilter)
    }
    
    // Sort
    result.sort((a, b) => {
      const diff = new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
      return sortDesc ? diff : -diff
    })
    
    return result
  }, [events, search, typeFilter, sortDesc])

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Event Log</h1>
        <p className="text-slate-500 mt-1">
          Complete history of board events
        </p>
      </div>
      
      {/* Filters */}
      <div className="flex flex-wrap items-center gap-4">
        <div className="relative flex-1 min-w-[200px] max-w-md">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search events..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
          />
        </div>
        
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 text-sm"
        >
          <option value="">All types</option>
          {eventTypes.map(type => (
            <option key={type} value={type}>{type}</option>
          ))}
        </select>
        
        <button
          onClick={() => setSortDesc(!sortDesc)}
          className="flex items-center gap-2 px-3 py-2 border border-slate-200 rounded-lg hover:bg-slate-50 text-sm"
        >
          {sortDesc ? (
            <>
              <ArrowDown className="w-4 h-4" />
              Newest first
            </>
          ) : (
            <>
              <ArrowUp className="w-4 h-4" />
              Oldest first
            </>
          )}
        </button>
      </div>
      
      {/* Stats */}
      <div className="flex items-center gap-4 text-sm text-slate-500">
        <Filter className="w-4 h-4" />
        <span>{filteredEvents.length} events</span>
        {search && <span>• filtered from {events.length}</span>}
      </div>
      
      {/* Event List */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        {/* Header */}
        <div className="flex items-center gap-4 px-4 py-3 bg-slate-50 border-b border-slate-200 text-xs font-medium text-slate-500 uppercase tracking-wide">
          <span className="w-16">ID</span>
          <span className="w-24">Type</span>
          <span className="flex-1">Pheromone</span>
          <span className="w-32">Source</span>
          <span className="w-32">Time</span>
          <span className="w-4" />
        </div>
        
        {/* Events */}
        {filteredEvents.length === 0 ? (
          <div className="p-12 text-center">
            <div className="w-12 h-12 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Zap className="w-6 h-6 text-slate-400" />
            </div>
            <h3 className="text-lg font-medium text-slate-800 mb-1">No events</h3>
            <p className="text-slate-500">
              {search || typeFilter ? 'No matches found' : 'Events will appear here as they occur'}
            </p>
          </div>
        ) : (
          <div className="max-h-[600px] overflow-y-auto">
            {filteredEvents.map((event, idx) => (
              <EventRow key={event.id} event={event} index={idx} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default EventLog

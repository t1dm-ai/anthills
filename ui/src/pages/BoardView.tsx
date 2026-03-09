import { useState, useMemo } from 'react'
import { useDashboardStore } from '../store'
import { Search, Filter, Clock, Tag, User } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import type { Pheromone } from '../types'

function PheromoneCard({ pheromone }: { pheromone: Pheromone }) {
  const [expanded, setExpanded] = useState(false)
  
  // Truncate payload for display
  const payloadPreview = useMemo(() => {
    const str = JSON.stringify(pheromone.payload, null, 2)
    if (str.length > 200 && !expanded) {
      return str.slice(0, 200) + '...'
    }
    return str
  }, [pheromone.payload, expanded])
  
  const isExpired = pheromone.ttl_seconds !== null && 
    new Date(pheromone.deposited_at).getTime() + (pheromone.ttl_seconds * 1000) < Date.now()
  
  return (
    <div className={`
      bg-white rounded-lg border p-4 transition-all
      ${isExpired ? 'border-red-200 bg-red-50/50' : 'border-slate-200 hover:border-emerald-300'}
    `}>
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <Tag className="w-4 h-4 text-emerald-500" />
          <span className="font-mono text-sm font-medium text-slate-800">
            {pheromone.type}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full">
            {pheromone.intensity.toFixed(1)}
          </span>
          {isExpired && (
            <span className="text-xs bg-red-100 text-red-600 px-2 py-0.5 rounded-full">
              Expired
            </span>
          )}
        </div>
      </div>
      
      <div className="space-y-2 text-sm">
        <div className="flex items-center gap-2 text-slate-500">
          <User className="w-3.5 h-3.5" />
          <span>From: <span className="text-slate-700">{pheromone.deposited_by}</span></span>
        </div>
        
        <div className="flex items-center gap-2 text-slate-500">
          <Clock className="w-3.5 h-3.5" />
          <span>{formatDistanceToNow(new Date(pheromone.deposited_at), { addSuffix: true })}</span>
        </div>
        
        {pheromone.trail_id && (
          <div className="text-xs text-slate-400">
            Trail: {pheromone.trail_id}
          </div>
        )}
      </div>
      
      {/* Payload */}
      <div className="mt-3 pt-3 border-t border-slate-100">
        <p className="text-xs text-slate-500 mb-1">Payload</p>
        <pre className="text-xs bg-slate-50 rounded p-2 overflow-x-auto text-slate-700">
          {payloadPreview}
        </pre>
        {JSON.stringify(pheromone.payload).length > 200 && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-xs text-emerald-600 hover:text-emerald-700 mt-1"
          >
            {expanded ? 'Show less' : 'Show more'}
          </button>
        )}
      </div>
    </div>
  )
}

function BoardView() {
  const { pheromones, boardStats } = useDashboardStore()
  const [search, setSearch] = useState('')
  const [showExpired, setShowExpired] = useState(false)
  
  const filteredPheromones = useMemo(() => {
    let result = [...pheromones]
    
    // Filter by search
    if (search) {
      const lower = search.toLowerCase()
      result = result.filter(p => 
        p.type.toLowerCase().includes(lower) ||
        p.deposited_by.toLowerCase().includes(lower) ||
        JSON.stringify(p.payload).toLowerCase().includes(lower)
      )
    }
    
    // Filter expired
    if (!showExpired) {
      result = result.filter(p => {
        if (p.ttl_seconds === null) return true
        return new Date(p.deposited_at).getTime() + (p.ttl_seconds * 1000) >= Date.now()
      })
    }
    
    // Sort by creation time, newest first
    return result.sort((a, b) => 
      new Date(b.deposited_at).getTime() - new Date(a.deposited_at).getTime()
    )
  }, [pheromones, search, showExpired])
  
  // Group by type
  const groupedPheromones = useMemo(() => {
    const groups: Record<string, Pheromone[]> = {}
    
    for (const p of filteredPheromones) {
      // Extract prefix (e.g., "task" from "task.created")
      const prefix = p.type.split('.')[0] || 'other'
      if (!groups[prefix]) groups[prefix] = []
      groups[prefix].push(p)
    }
    
    return groups
  }, [filteredPheromones])

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Pheromone Board</h1>
        <p className="text-slate-500 mt-1">
          Active pheromones in the colony
        </p>
      </div>
      
      {/* Stats Summary */}
      <div className="flex gap-4 text-sm">
        <div className="bg-white rounded-lg border border-slate-200 px-4 py-2">
          <span className="text-slate-500">Total:</span>
          <span className="ml-2 font-semibold text-slate-800">{boardStats.total_pheromones}</span>
        </div>
        <div className="bg-white rounded-lg border border-slate-200 px-4 py-2">
          <span className="text-slate-500">Active:</span>
          <span className="ml-2 font-semibold text-emerald-600">{boardStats.active_pheromones}</span>
        </div>
        <div className="bg-white rounded-lg border border-slate-200 px-4 py-2">
          <span className="text-slate-500">Evaporated:</span>
          <span className="ml-2 font-semibold text-orange-600">{boardStats.evaporated_count}</span>
        </div>
      </div>
      
      {/* Filters */}
      <div className="flex flex-wrap gap-4">
        <div className="relative flex-1 min-w-[200px] max-w-md">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search types, sources, or payloads..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
          />
        </div>
        
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={showExpired}
            onChange={(e) => setShowExpired(e.target.checked)}
            className="w-4 h-4 text-emerald-500 rounded focus:ring-emerald-500"
          />
          <span className="text-sm text-slate-600">Show expired</span>
        </label>
      </div>
      
      {/* Stats Bar */}
      <div className="flex items-center gap-4 text-sm text-slate-500">
        <Filter className="w-4 h-4" />
        <span>{filteredPheromones.length} pheromones</span>
        <span>•</span>
        <span>{Object.keys(groupedPheromones).length} groups</span>
      </div>
      
      {/* Pheromone Groups */}
      {Object.keys(groupedPheromones).length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
          <div className="w-12 h-12 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Tag className="w-6 h-6 text-slate-400" />
          </div>
          <h3 className="text-lg font-medium text-slate-800 mb-1">No pheromones</h3>
          <p className="text-slate-500">
            {search ? 'No matches found for your search' : 'The board is empty'}
          </p>
        </div>
      ) : (
        <div className="space-y-8">
          {Object.entries(groupedPheromones).map(([prefix, items]) => (
            <div key={prefix}>
              <h2 className="text-lg font-semibold text-slate-800 mb-3 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-500" />
                {prefix}
                <span className="text-sm font-normal text-slate-400">({items.length})</span>
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {items.map(p => (
                  <PheromoneCard key={p.id} pheromone={p} />
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default BoardView

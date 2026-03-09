import { create } from 'zustand'
import type { Pheromone, BoardEvent, Worker, Colony, BoardStats, WorkerStats, WSMessage } from './types'

interface DashboardStore {
  // State
  colony: Colony | null
  pheromones: Pheromone[]
  events: BoardEvent[]
  workers: Worker[]
  connected: boolean
  error: string | null
  
  // Computed stats
  boardStats: BoardStats
  workerStats: WorkerStats
  
  // Actions
  setColony: (colony: Colony) => void
  addPheromone: (pheromone: Pheromone) => void
  removePheromone: (pheromoneId: string) => void
  addEvent: (event: BoardEvent) => void
  updateWorker: (workerId: string, updates: Partial<Worker>) => void
  setConnected: (connected: boolean) => void
  setError: (error: string | null) => void
  handleWSMessage: (message: WSMessage) => void
  reset: () => void
}

const computeBoardStats = (pheromones: Pheromone[], events: BoardEvent[]): BoardStats => {
  const evaporatedIds = new Set(
    events.filter(e => e.event_type === 'evaporated').map(e => e.pheromone_id)
  )
  
  const activePheromones = pheromones.filter(p => !evaporatedIds.has(p.id))
  
  const pheromonesByType: Record<string, number> = {}
  activePheromones.forEach(p => {
    pheromonesByType[p.type] = (pheromonesByType[p.type] || 0) + 1
  })
  
  return {
    total_pheromones: pheromones.length,
    active_pheromones: activePheromones.length,
    evaporated_count: evaporatedIds.size,
    pheromones_by_type: pheromonesByType,
  }
}

const computeWorkerStats = (workers: Worker[]): WorkerStats => {
  return {
    total_workers: workers.length,
    busy_workers: workers.filter(w => w.status === 'busy').length,
    idle_workers: workers.filter(w => w.status === 'idle').length,
    error_workers: workers.filter(w => w.status === 'error').length,
    total_processed: workers.reduce((sum, w) => sum + w.processed_count, 0),
    total_errors: workers.reduce((sum, w) => sum + w.error_count, 0),
  }
}

const initialState = {
  colony: null,
  pheromones: [],
  events: [],
  workers: [],
  connected: false,
  error: null,
  boardStats: {
    total_pheromones: 0,
    active_pheromones: 0,
    evaporated_count: 0,
    pheromones_by_type: {},
  },
  workerStats: {
    total_workers: 0,
    busy_workers: 0,
    idle_workers: 0,
    error_workers: 0,
    total_processed: 0,
    total_errors: 0,
  },
}

export const useDashboardStore = create<DashboardStore>((set, get) => ({
  ...initialState,
  
  setColony: (colony) => set({ colony }),
  
  addPheromone: (pheromone) => set((state) => {
    const pheromones = [pheromone, ...state.pheromones].slice(0, 1000) // Keep last 1000
    return {
      pheromones,
      boardStats: computeBoardStats(pheromones, state.events),
    }
  }),
  
  removePheromone: (pheromoneId) => set((state) => {
    const event: BoardEvent = {
      id: crypto.randomUUID(),
      event_type: 'evaporated',
      pheromone_id: pheromoneId,
      pheromone: null,
      timestamp: new Date().toISOString(),
    }
    const events = [event, ...state.events].slice(0, 1000)
    return {
      events,
      boardStats: computeBoardStats(state.pheromones, events),
    }
  }),
  
  addEvent: (event) => set((state) => {
    const events = [event, ...state.events].slice(0, 1000)
    return {
      events,
      boardStats: computeBoardStats(state.pheromones, events),
    }
  }),
  
  updateWorker: (workerId, updates) => set((state) => {
    const workers = state.workers.map(w =>
      w.id === workerId ? { ...w, ...updates } : w
    )
    return {
      workers,
      workerStats: computeWorkerStats(workers),
    }
  }),
  
  setConnected: (connected) => set({ connected }),
  
  setError: (error) => set({ error }),
  
  handleWSMessage: (message) => {
    const { addPheromone, removePheromone, updateWorker, setColony } = get()
    
    switch (message.type) {
      case 'colony_state':
        setColony(message.data)
        break
      case 'pheromone_deposited':
        addPheromone(message.data)
        break
      case 'pheromone_evaporated':
        removePheromone(message.data.pheromone_id)
        break
      case 'worker_started':
        updateWorker(message.data.worker_id, { status: 'busy' })
        break
      case 'worker_completed':
        updateWorker(message.data.worker_id, {
          status: 'idle',
          processed_count: (get().workers.find(w => w.id === message.data.worker_id)?.processed_count || 0) + 1,
          last_active: new Date().toISOString(),
        })
        break
      case 'worker_error':
        updateWorker(message.data.worker_id, {
          status: 'error',
          error_count: (get().workers.find(w => w.id === message.data.worker_id)?.error_count || 0) + 1,
        })
        break
      case 'board_snapshot':
        set({
          pheromones: message.data.pheromones,
          events: message.data.events,
          boardStats: computeBoardStats(message.data.pheromones, message.data.events),
        })
        break
    }
  },
  
  reset: () => set(initialState),
}))

import { create } from 'zustand'
import type {
  Pheromone, BoardEvent, Worker, Colony, BoardStats, WorkerStats,
  WSMessage, Technician, JobPayload, LedgerEntry,
} from './types'

const now = new Date()
const ago = (minutes: number) =>
  new Date(now.getTime() - minutes * 60 * 1000).toISOString()

// ─── Mock Data ────────────────────────────────────────────────────────────────

const mockTechnicians: Technician[] = [
  {
    id: 'tech-1',
    name: 'Alex Rivera',
    status: 'on_site',
    region: 'North District',
    certifications: ['EPA 608', 'NATE'],
    current_job_id: 'trail-4',
    jobs_today: 2,
    phone: '(555) 101-0001',
  },
  {
    id: 'tech-2',
    name: 'Maria Chen',
    status: 'en_route',
    region: 'South District',
    certifications: ['EPA 608'],
    current_job_id: 'trail-3',
    jobs_today: 1,
    phone: '(555) 101-0002',
  },
  {
    id: 'tech-3',
    name: 'Marcus Johnson',
    status: 'available',
    region: 'East District',
    certifications: ['EPA 608', 'NATE', 'R-410A'],
    current_job_id: null,
    jobs_today: 3,
    phone: '(555) 101-0003',
  },
  {
    id: 'tech-4',
    name: 'Sarah Kim',
    status: 'on_site',
    region: 'West District',
    certifications: ['EPA 608', 'NATE'],
    current_job_id: 'trail-5',
    jobs_today: 2,
    phone: '(555) 101-0004',
  },
]

const mockPheromones: Pheromone[] = [
  {
    id: 'phero-1',
    type: 'job.requested',
    payload: {
      customer: 'Lisa Park',
      address: '321 Elm St, Springfield',
      phone: '(555) 200-0101',
      issue: 'AC',
      urgency: 'urgent',
      notes: 'AC not blowing cold air at all. Unit is running but warm.',
    },
    intensity: 1.0,
    deposited_by: 'system',
    deposited_at: ago(2),
    ttl_seconds: null,
    trail_id: 'trail-1',
    metadata: {},
  },
  {
    id: 'phero-2',
    type: 'job.qualified',
    payload: {
      customer: 'Tom Brown',
      address: '555 Broadway, Springfield',
      phone: '(555) 200-0102',
      issue: 'Heating',
      urgency: 'standard',
      notes: 'Furnace kicks on but shuts off after 2 minutes.',
    },
    intensity: 1.0,
    deposited_by: 'lead-qualifier',
    deposited_at: ago(15),
    ttl_seconds: null,
    trail_id: 'trail-2',
    metadata: {},
  },
  {
    id: 'phero-3',
    type: 'job.dispatched',
    payload: {
      customer: 'Amy Wilson',
      address: '789 Pine St, Springfield',
      phone: '(555) 200-0103',
      issue: 'Heating',
      urgency: 'standard',
      notes: 'No heat in master bedroom.',
      tech_id: 'tech-2',
      tech_name: 'Maria Chen',
    },
    intensity: 1.0,
    deposited_by: 'dispatcher',
    deposited_at: ago(32),
    ttl_seconds: null,
    trail_id: 'trail-3',
    metadata: {},
  },
  {
    id: 'phero-4',
    type: 'job.on_site',
    payload: {
      customer: 'Carlos Mendez',
      address: '456 Oak Ave, Springfield',
      phone: '(555) 200-0104',
      issue: 'Emergency',
      urgency: 'emergency',
      notes: 'Commercial refrigeration unit failure. Business at risk.',
      tech_id: 'tech-1',
      tech_name: 'Alex Rivera',
    },
    intensity: 1.0,
    deposited_by: 'system',
    deposited_at: ago(58),
    ttl_seconds: null,
    trail_id: 'trail-4',
    metadata: {},
  },
  {
    id: 'phero-5',
    type: 'job.on_site',
    payload: {
      customer: 'Helen Foster',
      address: '123 Main St, Springfield',
      phone: '(555) 200-0105',
      issue: 'Maintenance',
      urgency: 'low',
      notes: 'Annual HVAC maintenance checkup.',
      tech_id: 'tech-4',
      tech_name: 'Sarah Kim',
    },
    intensity: 1.0,
    deposited_by: 'system',
    deposited_at: ago(45),
    ttl_seconds: null,
    trail_id: 'trail-5',
    metadata: {},
  },
  {
    id: 'phero-6',
    type: 'job.completed',
    payload: {
      customer: 'David Lee',
      address: '222 Maple Dr, Springfield',
      phone: '(555) 200-0106',
      issue: 'AC',
      urgency: 'standard',
      notes: 'Replaced capacitor and recharged refrigerant.',
      tech_id: 'tech-1',
      tech_name: 'Alex Rivera',
    },
    intensity: 1.0,
    deposited_by: 'system',
    deposited_at: ago(180),
    ttl_seconds: null,
    trail_id: 'trail-6',
    metadata: {},
  },
]

const mockEvents: BoardEvent[] = mockPheromones.map((p) => ({
  id: `evt-${p.id}`,
  event_type: 'deposit' as const,
  pheromone_id: p.id,
  pheromone: p,
  timestamp: p.deposited_at,
}))

const mockWorkers: Worker[] = [
  {
    id: 'agent-lead',
    name: 'LeadQualifier',
    reacts_to: 'job.requested',
    status: 'busy',
    processed_count: 42,
    error_count: 1,
    last_active: ago(2),
  },
  {
    id: 'agent-dispatch',
    name: 'Dispatcher',
    reacts_to: 'job.qualified',
    status: 'idle',
    processed_count: 38,
    error_count: 0,
    last_active: ago(15),
  },
  {
    id: 'agent-invoice',
    name: 'InvoiceProcessor',
    reacts_to: 'job.completed',
    status: 'idle',
    processed_count: 31,
    error_count: 2,
    last_active: ago(180),
  },
  {
    id: 'agent-followup',
    name: 'FollowupAgent',
    reacts_to: 'invoice.paid',
    status: 'idle',
    processed_count: 28,
    error_count: 0,
    last_active: ago(240),
  },
]

const mockColony: Colony = {
  id: 'colony-hvac',
  name: 'CoolFlow HVAC',
  status: 'running',
  workers: mockWorkers,
  pheromone_count: mockPheromones.length,
  event_count: mockEvents.length,
  started_at: new Date(now.getFullYear(), now.getMonth(), now.getDate(), 8, 0, 0).toISOString(),
}

// ─── Store ────────────────────────────────────────────────────────────────────

interface DashboardStore {
  colony: Colony | null
  pheromones: Pheromone[]
  events: BoardEvent[]
  workers: Worker[]
  technicians: Technician[]
  ledger: LedgerEntry[]
  chainValid: boolean
  connected: boolean
  error: string | null
  boardStats: BoardStats
  workerStats: WorkerStats

  setColony: (colony: Colony) => void
  addPheromone: (pheromone: Pheromone) => void
  removePheromone: (pheromoneId: string) => void
  addEvent: (event: BoardEvent) => void
  updateWorker: (workerId: string, updates: Partial<Worker>) => void
  upsertLedgerEntry: (entry: LedgerEntry) => void
  setConnected: (connected: boolean) => void
  setError: (error: string | null) => void
  handleWSMessage: (message: WSMessage) => void
  addServiceRequest: (payload: JobPayload) => void
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

const computeWorkerStats = (workers: Worker[]): WorkerStats => ({
  total_workers: workers.length,
  busy_workers: workers.filter(w => w.status === 'busy').length,
  idle_workers: workers.filter(w => w.status === 'idle').length,
  error_workers: workers.filter(w => w.status === 'error').length,
  total_processed: workers.reduce((sum, w) => sum + w.processed_count, 0),
  total_errors: workers.reduce((sum, w) => sum + w.error_count, 0),
})

const initialState = {
  colony: mockColony,
  pheromones: mockPheromones,
  events: mockEvents,
  workers: mockWorkers,
  technicians: mockTechnicians,
  ledger: [] as LedgerEntry[],
  chainValid: true,
  connected: true,
  error: null,
  boardStats: computeBoardStats(mockPheromones, mockEvents),
  workerStats: computeWorkerStats(mockWorkers),
}

export const useDashboardStore = create<DashboardStore>((set, get) => ({
  ...initialState,

  setColony: (colony) => set({ colony }),

  addPheromone: (pheromone) =>
    set((state) => {
      const pheromones = [pheromone, ...state.pheromones].slice(0, 1000)
      return { pheromones, boardStats: computeBoardStats(pheromones, state.events) }
    }),

  removePheromone: (pheromoneId) =>
    set((state) => {
      const event: BoardEvent = {
        id: crypto.randomUUID(),
        event_type: 'evaporated',
        pheromone_id: pheromoneId,
        pheromone: null,
        timestamp: new Date().toISOString(),
      }
      const events = [event, ...state.events].slice(0, 1000)
      return { events, boardStats: computeBoardStats(state.pheromones, events) }
    }),

  addEvent: (event) =>
    set((state) => {
      const events = [event, ...state.events].slice(0, 1000)
      return { events, boardStats: computeBoardStats(state.pheromones, events) }
    }),

  updateWorker: (workerId, updates) =>
    set((state) => {
      const workers = state.workers.map(w =>
        w.id === workerId ? { ...w, ...updates } : w
      )
      return { workers, workerStats: computeWorkerStats(workers) }
    }),

  upsertLedgerEntry: (entry) =>
    set((state) => {
      const idx = state.ledger.findIndex(e => e.id === entry.id)
      const ledger = idx >= 0
        ? state.ledger.map((e, i) => i === idx ? entry : e)
        : [entry, ...state.ledger].slice(0, 500)
      return { ledger }
    }),

  setConnected: (connected) => set({ connected }),

  setError: (error) => set({ error }),

  addServiceRequest: (payload) => {
    // Send to backend — the real agents will pick it up and broadcast back via WS
    fetch('http://localhost:8000/api/deposit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type: 'job.requested', payload }),
    }).catch(() => {
      // Backend unreachable — fall back to local-only state so the UI still works
      set((state) => {
        const pheromone: Pheromone = {
          id: crypto.randomUUID(),
          type: 'job.requested',
          payload: payload as unknown as Record<string, unknown>,
          intensity: 1.0,
          deposited_by: 'ui',
          deposited_at: new Date().toISOString(),
          ttl_seconds: null,
          trail_id: crypto.randomUUID(),
          metadata: {},
        }
        const event: BoardEvent = {
          id: crypto.randomUUID(),
          event_type: 'deposit',
          pheromone_id: pheromone.id,
          pheromone,
          timestamp: pheromone.deposited_at,
        }
        const pheromones = [pheromone, ...state.pheromones].slice(0, 1000)
        const events = [event, ...state.events].slice(0, 1000)
        return { pheromones, events, boardStats: computeBoardStats(pheromones, events) }
      })
    })
  },

  handleWSMessage: (message) => {
    const { addPheromone, removePheromone, updateWorker } = get()
    switch (message.type) {
      case 'colony_state': {
        const workers = message.data.workers || []
        set({
          colony: message.data,
          workers,
          workerStats: computeWorkerStats(workers),
        })
        break
      }
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
          processed_count:
            (get().workers.find(w => w.id === message.data.worker_id)?.processed_count || 0) + 1,
          last_active: new Date().toISOString(),
        })
        break
      case 'worker_error':
        updateWorker(message.data.worker_id, {
          status: 'error',
          error_count:
            (get().workers.find(w => w.id === message.data.worker_id)?.error_count || 0) + 1,
        })
        break
      case 'board_snapshot':
        set({
          pheromones: message.data.pheromones,
          events: message.data.events,
          boardStats: computeBoardStats(message.data.pheromones, message.data.events),
        })
        break
      case 'ledger_snapshot':
        set({
          ledger: message.data.entries,
          chainValid: message.data.chain_valid,
        })
        break
      case 'ledger_entry':
        get().upsertLedgerEntry(message.data)
        break
    }
  },

  reset: () => set(initialState),
}))

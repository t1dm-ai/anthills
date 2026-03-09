// Types for the Anthills dashboard

export interface Pheromone {
  id: string
  type: string
  payload: Record<string, unknown>
  intensity: number
  deposited_by: string
  deposited_at: string
  ttl_seconds: number | null
  trail_id: string | null
  metadata: Record<string, unknown>
}

export interface BoardEvent {
  id: string
  event_type: 'deposit' | 'evaporated'
  pheromone_id: string
  pheromone: Pheromone | null
  timestamp: string
}

export interface Worker {
  id: string
  name: string
  reacts_to: string
  status: 'idle' | 'busy' | 'error'
  processed_count: number
  error_count: number
  last_active: string | null
}

export interface Colony {
  id: string
  name: string
  status: 'running' | 'stopped' | 'paused'
  workers: Worker[]
  pheromone_count: number
  event_count: number
  started_at: string | null
}

export interface BoardStats {
  total_pheromones: number
  active_pheromones: number
  evaporated_count: number
  pheromones_by_type: Record<string, number>
}

export interface WorkerStats {
  total_workers: number
  busy_workers: number
  idle_workers: number
  error_workers: number
  total_processed: number
  total_errors: number
}

export interface DashboardState {
  colony: Colony | null
  pheromones: Pheromone[]
  events: BoardEvent[]
  workers: Worker[]
  boardStats: BoardStats
  workerStats: WorkerStats
  connected: boolean
  error: string | null
}

// WebSocket message types
export type WSMessage =
  | { type: 'colony_state'; data: Colony }
  | { type: 'pheromone_deposited'; data: Pheromone }
  | { type: 'pheromone_evaporated'; data: { pheromone_id: string } }
  | { type: 'worker_started'; data: { worker_id: string; pheromone_id: string } }
  | { type: 'worker_completed'; data: { worker_id: string; pheromone_id: string } }
  | { type: 'worker_error'; data: { worker_id: string; error: string } }
  | { type: 'board_snapshot'; data: { pheromones: Pheromone[]; events: BoardEvent[] } }

// Types for the CoolFlow HVAC Operations dashboard

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

// ─── Ledger ───────────────────────────────────────────────────────────────────

export interface LedgerEntry {
  // Identity
  id: string
  worker_id: string
  worker_name: string
  invocation_id: string

  // Trigger
  trigger_pheromone_id: string
  trigger_pheromone_type: string
  trail_id: string
  input_payload: Record<string, unknown>

  // Timing
  started_at: string
  completed_at: string | null
  duration_ms: number | null

  // Outcome
  status: 'running' | 'completed' | 'error'
  error: string | null
  output_pheromone_type: string | null
  output_payload: Record<string, unknown> | null

  // LLM-specific
  messages: Array<{ role: string; content: string }> | null
  raw_response_text: string | null
  thinking: string[] | null
  token_usage: { input_tokens: number; output_tokens: number } | null
  model: string | null

  // Chain
  prev_hash: string | null
  hash: string | null
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
  | { type: 'ledger_snapshot'; data: { entries: LedgerEntry[]; chain_valid: boolean } }
  | { type: 'ledger_entry'; data: LedgerEntry }

// HVAC-specific types
export type IssueType = 'AC' | 'Heating' | 'Maintenance' | 'Emergency'
export type Urgency = 'low' | 'standard' | 'urgent' | 'emergency'

export interface JobPayload {
  customer: string
  address: string
  phone: string
  issue: IssueType
  urgency: Urgency
  notes?: string
  tech_id?: string
  tech_name?: string
}

export interface Technician {
  id: string
  name: string
  status: 'available' | 'en_route' | 'on_site'
  region: string
  certifications: string[]
  current_job_id: string | null
  jobs_today: number
  phone: string
}

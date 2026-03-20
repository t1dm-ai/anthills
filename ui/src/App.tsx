import { useEffect } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout.tsx'
import Dashboard from './pages/Dashboard.tsx'
import BoardView from './pages/BoardView.tsx'
import WorkersView from './pages/WorkersView.tsx'
import EventLog from './pages/EventLog.tsx'
import ServiceRequests from './pages/ServiceRequests.tsx'
import LedgerView from './pages/LedgerView.tsx'
import { useDashboardStore } from './store.ts'

const WS_URL = 'ws://localhost:8000/ws'

function WebSocketConnector() {
  const { handleWSMessage, setConnected, setError } = useDashboardStore()

  useEffect(() => {
    let ws: WebSocket | null = null
    let reconnectTimer: ReturnType<typeof setTimeout>
    let unmounted = false

    function connect() {
      if (unmounted) return
      try {
        ws = new WebSocket(WS_URL)

        ws.onopen = () => {
          setConnected(true)
          setError(null)
          console.log('[WS] Connected to CoolFlow backend')
        }

        ws.onmessage = (event) => {
          try {
            const msg = JSON.parse(event.data)
            handleWSMessage(msg)
          } catch (e) {
            console.error('[WS] Parse error', e)
          }
        }

        ws.onclose = () => {
          if (!unmounted) {
            setConnected(false)
            reconnectTimer = setTimeout(connect, 3000)
          }
        }

        ws.onerror = () => {
          setError('Cannot connect to backend (ws://localhost:8000)')
          ws?.close()
        }
      } catch {
        reconnectTimer = setTimeout(connect, 3000)
      }
    }

    connect()

    return () => {
      unmounted = true
      clearTimeout(reconnectTimer)
      ws?.close()
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return null
}

function App() {
  return (
    <BrowserRouter>
      <WebSocketConnector />
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="board" element={<BoardView />} />
          <Route path="workers" element={<WorkersView />} />
          <Route path="requests" element={<ServiceRequests />} />
          <Route path="events" element={<EventLog />} />
          <Route path="ledger" element={<LedgerView />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App

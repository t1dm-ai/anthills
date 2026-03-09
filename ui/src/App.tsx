import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout.tsx'
import Dashboard from './pages/Dashboard.tsx'
import BoardView from './pages/BoardView.tsx'
import WorkersView from './pages/WorkersView.tsx'
import EventLog from './pages/EventLog.tsx'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="board" element={<BoardView />} />
          <Route path="workers" element={<WorkersView />} />
          <Route path="events" element={<EventLog />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App

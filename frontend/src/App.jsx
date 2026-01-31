import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import IncidentList from './pages/IncidentList'
import IncidentDetail from './pages/IncidentDetail'
import CreateIncident from './pages/CreateIncident'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<IncidentList />} />
        <Route path="/incidents/new" element={<CreateIncident />} />
        <Route path="/incidents/:id" element={<IncidentDetail />} />
      </Routes>
    </Layout>
  )
}

export default App

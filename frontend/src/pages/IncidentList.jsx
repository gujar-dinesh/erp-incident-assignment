import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { incidentService } from '../services/api'
import StatusBadge from '../components/StatusBadge'
import './IncidentList.css'

function IncidentList() {
  const [incidents, setIncidents] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [filter, setFilter] = useState({ severity: '', module: '', status: 'open' })
  const [nextToken, setNextToken] = useState(null)
  const [hasMore, setHasMore] = useState(false)

  useEffect(() => {
    loadIncidents()
  }, [filter])

  const loadIncidents = async (reset = true) => {
    try {
      setLoading(true)
      setError(null)
      
      const params = {
        limit: 50,
        // Send 'all' when "All Statuses" is selected, otherwise send the status value
        ...(filter.status === '' ? { status: 'all' } : filter.status && { status: filter.status }),
        ...(filter.severity && { severity: filter.severity }),
        ...(filter.module && { erp_module: filter.module }),
        ...(nextToken && !reset && { next_token: nextToken })
      }
      
      // Debug logging
      console.log('🔍 Filter status:', filter.status, '→ Params:', params)
      
      const response = await incidentService.getAll(params)
      
      if (reset) {
        setIncidents(response.incidents || [])
      } else {
        setIncidents(prev => [...prev, ...(response.incidents || [])])
      }
      
      setNextToken(response.next_token || null)
      setHasMore(!!response.next_token)
    } catch (err) {
      setError('Failed to load incidents. Please try again.')
      console.error('Error loading incidents:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleLoadMore = () => {
    if (hasMore && !loading) {
      loadIncidents(false)
    }
  }

  const handleFilterChange = (newFilter) => {
    setFilter(newFilter)
    setNextToken(null)
    setHasMore(false)
  }

  const formatDate = (dateString) => {
    const date = new Date(dateString)
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  if (loading) {
    return <div className="loading">Loading incidents...</div>
  }

  if (error) {
    return (
      <div className="error-container">
        <p className="error">{error}</p>
        <button onClick={loadIncidents} className="retry-button">
          Retry
        </button>
      </div>
    )
  }

  return (
    <div className="incident-list">
      <div className="list-header">
        <h1>Incidents</h1>
        <Link to="/incidents/new" className="new-incident-button">
          Create New Incident
        </Link>
      </div>

      <div className="filters">
        <div className="filter-group">
          <label htmlFor="status-filter">Filter by Status:</label>
          <select
            id="status-filter"
            value={filter.status}
            onChange={(e) => handleFilterChange({ ...filter, status: e.target.value })}
          >
            <option value="open">Open</option>
            <option value="in_progress">In Progress</option>
            <option value="resolved">Resolved</option>
            <option value="closed">Closed</option>
            <option value="">All Statuses</option>
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="severity-filter">Filter by Severity:</label>
          <select
            id="severity-filter"
            value={filter.severity}
            onChange={(e) => handleFilterChange({ ...filter, severity: e.target.value })}
          >
            <option value="">All</option>
            <option value="P1">P1</option>
            <option value="P2">P2</option>
            <option value="P3">P3</option>
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="module-filter">Filter by Module:</label>
          <select
            id="module-filter"
            value={filter.module}
            onChange={(e) => handleFilterChange({ ...filter, module: e.target.value })}
          >
            <option value="">All</option>
            <option value="AP">AP</option>
            <option value="AR">AR</option>
            <option value="GL">GL</option>
            <option value="Inventory">Inventory</option>
            <option value="HR">HR</option>
            <option value="Payroll">Payroll</option>
          </select>
        </div>
      </div>

      {incidents.length === 0 && !loading ? (
        <div className="empty-state">
          <p>No incidents found.</p>
          <Link to="/incidents/new" className="new-incident-button">
            Create Your First Incident
          </Link>
        </div>
      ) : (
        <>
          <div className="incidents-grid">
            {incidents.map((incident) => (
            <Link
              key={incident.id}
              to={`/incidents/${incident.id}`}
              className="incident-card"
            >
              <div className="card-header">
                <h3>{incident.title}</h3>
                <StatusBadge status={incident.status} severity={incident.severity} />
              </div>
              <div className="card-body">
                <p className="description">{incident.description.substring(0, 150)}...</p>
                <div className="card-meta">
                  <span className="meta-item">
                    <strong>Module:</strong> {incident.erp_module}
                  </span>
                  <span className="meta-item">
                    <strong>Category:</strong> {incident.category}
                  </span>
                  <span className="meta-item">
                    <strong>Environment:</strong> {incident.environment}
                  </span>
                </div>
              </div>
              <div className="card-footer">
                <span className="timestamp">
                  Created: {formatDate(incident.created_at)}
                </span>
              </div>
            </Link>
          ))}
          </div>
          
          {hasMore && (
            <div className="load-more-container">
              <button 
                onClick={handleLoadMore} 
                className="load-more-button"
                disabled={loading}
              >
                {loading ? 'Loading...' : 'Load More'}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default IncidentList

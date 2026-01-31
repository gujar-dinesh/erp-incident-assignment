import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { incidentService } from '../services/api'
import StatusBadge from '../components/StatusBadge'
import './IncidentDetail.css'

function IncidentDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [incident, setIncident] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [updating, setUpdating] = useState(false)
  const [statusUpdate, setStatusUpdate] = useState('')

  useEffect(() => {
    loadIncident()
  }, [id])

  const loadIncident = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await incidentService.getById(id)
      setIncident(data)
      setStatusUpdate(data.status)
    } catch (err) {
      setError('Failed to load incident. Please try again.')
      console.error('Error loading incident:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleStatusUpdate = async (newStatus) => {
    if (newStatus === incident.status) return

    try {
      setUpdating(true)
      const updated = await incidentService.update(id, { status: newStatus })
      setIncident(updated)
      setStatusUpdate(newStatus)
    } catch (err) {
      setError('Failed to update status. Please try again.')
      console.error('Error updating incident:', err)
    } finally {
      setUpdating(false)
    }
  }

  const formatDate = (dateString) => {
    const date = new Date(dateString)
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  if (loading) {
    return <div className="loading">Loading incident details...</div>
  }

  if (error && !incident) {
    return (
      <div className="error-container">
        <p className="error">{error}</p>
        <button onClick={() => navigate('/')} className="back-button">
          Back to List
        </button>
      </div>
    )
  }

  if (!incident) {
    return (
      <div className="error-container">
        <p className="error">Incident not found</p>
        <button onClick={() => navigate('/')} className="back-button">
          Back to List
        </button>
      </div>
    )
  }

  return (
    <div className="incident-detail">
      <div className="detail-header">
        <button onClick={() => navigate('/')} className="back-link">
          ← Back to Incidents
        </button>
        <div className="header-actions">
          <StatusBadge status={incident.status} severity={incident.severity} />
          <select
            value={statusUpdate}
            onChange={(e) => handleStatusUpdate(e.target.value)}
            disabled={updating}
            className="status-select"
          >
            <option value="open">Open</option>
            <option value="in_progress">In Progress</option>
            <option value="resolved">Resolved</option>
            <option value="closed">Closed</option>
          </select>
        </div>
      </div>

      <div className="detail-content">
        <div className="detail-main">
          <h1>{incident.title}</h1>
          
          <div className="detail-section">
            <h2>Description</h2>
            <p className="description-text">{incident.description}</p>
          </div>

          {incident.summary && (
            <div className="detail-section">
              <h2>Summary</h2>
              <p className="summary-text">{incident.summary}</p>
            </div>
          )}

          {incident.suggested_action && (
            <div className="detail-section">
              <h2>Suggested Action</h2>
              <p className="action-text">{incident.suggested_action}</p>
            </div>
          )}
        </div>

        <div className="detail-sidebar">
          <div className="info-card">
            <h3>Incident Details</h3>
            <dl className="info-list">
              <div className="info-item">
                <dt>Status</dt>
                <dd>{incident.status.replace('_', ' ').toUpperCase()}</dd>
              </div>
              <div className="info-item">
                <dt>Severity</dt>
                <dd>{incident.severity}</dd>
              </div>
              <div className="info-item">
                <dt>Category</dt>
                <dd>{incident.category}</dd>
              </div>
              <div className="info-item">
                <dt>ERP Module</dt>
                <dd>{incident.erp_module}</dd>
              </div>
              <div className="info-item">
                <dt>Environment</dt>
                <dd>{incident.environment}</dd>
              </div>
              <div className="info-item">
                <dt>Business Unit</dt>
                <dd>{incident.business_unit}</dd>
              </div>
            </dl>
          </div>

          <div className="info-card">
            <h3>Timestamps</h3>
            <dl className="info-list">
              <div className="info-item">
                <dt>Created</dt>
                <dd>{formatDate(incident.created_at)}</dd>
              </div>
              <div className="info-item">
                <dt>Last Updated</dt>
                <dd>{formatDate(incident.updated_at)}</dd>
              </div>
            </dl>
          </div>
        </div>
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}
    </div>
  )
}

export default IncidentDetail

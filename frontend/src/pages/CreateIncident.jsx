import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { incidentService } from '../services/api'
import './CreateIncident.css'

function CreateIncident() {
  const navigate = useNavigate()
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    erp_module: 'AP',
    environment: 'Prod',
    business_unit: '',
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const incident = await incidentService.create(formData)
      navigate(`/incidents/${incident.id}`)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create incident. Please try again.')
      console.error('Error creating incident:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="create-incident">
      <h1>Create New Incident</h1>
      
      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="incident-form">
        <div className="form-group">
          <label htmlFor="title">Title *</label>
          <input
            type="text"
            id="title"
            name="title"
            value={formData.title}
            onChange={handleChange}
            required
            maxLength={200}
            placeholder="Brief description of the incident"
          />
        </div>

        <div className="form-group">
          <label htmlFor="description">Description *</label>
          <textarea
            id="description"
            name="description"
            value={formData.description}
            onChange={handleChange}
            required
            rows={6}
            placeholder="Detailed description of the incident, including any error messages or symptoms"
          />
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="erp_module">ERP Module *</label>
            <select
              id="erp_module"
              name="erp_module"
              value={formData.erp_module}
              onChange={handleChange}
              required
            >
              <option value="AP">AP (Accounts Payable)</option>
              <option value="AR">AR (Accounts Receivable)</option>
              <option value="GL">GL (General Ledger)</option>
              <option value="Inventory">Inventory</option>
              <option value="HR">HR (Human Resources)</option>
              <option value="Payroll">Payroll</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="environment">Environment *</label>
            <select
              id="environment"
              name="environment"
              value={formData.environment}
              onChange={handleChange}
              required
            >
              <option value="Prod">Production</option>
              <option value="Test">Test</option>
            </select>
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="business_unit">Business Unit *</label>
          <input
            type="text"
            id="business_unit"
            name="business_unit"
            value={formData.business_unit}
            onChange={handleChange}
            required
            maxLength={100}
            placeholder="e.g., Finance, Operations, HR"
          />
        </div>

        <div className="form-actions">
          <button
            type="button"
            onClick={() => navigate('/')}
            className="cancel-button"
            disabled={loading}
          >
            Cancel
          </button>
          <button
            type="submit"
            className="submit-button"
            disabled={loading}
          >
            {loading ? 'Creating...' : 'Create Incident'}
          </button>
        </div>
      </form>

      <div className="form-info">
        <p>
          <strong>Note:</strong> The system will automatically enrich your incident with:
        </p>
        <ul>
          <li>Severity level (P1, P2, or P3) based on content analysis</li>
          <li>Category classification (Configuration, Data, Integration, Security, etc.)</li>
          <li>Summary and suggested next actions</li>
        </ul>
      </div>
    </div>
  )
}

export default CreateIncident

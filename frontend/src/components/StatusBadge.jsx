import './StatusBadge.css'

function StatusBadge({ status, severity }) {
  const getStatusClass = (status) => {
    const statusMap = {
      open: 'status-open',
      in_progress: 'status-in-progress',
      resolved: 'status-resolved',
      closed: 'status-closed',
    }
    return statusMap[status] || 'status-default'
  }

  const getSeverityClass = (severity) => {
    const severityMap = {
      P1: 'severity-p1',
      P2: 'severity-p2',
      P3: 'severity-p3',
    }
    return severityMap[severity] || 'severity-default'
  }

  return (
    <div className="badge-container">
      {status && (
        <span className={`badge ${getStatusClass(status)}`}>
          {status.replace('_', ' ').toUpperCase()}
        </span>
      )}
      {severity && (
        <span className={`badge ${getSeverityClass(severity)}`}>
          {severity}
        </span>
      )}
    </div>
  )
}

export default StatusBadge

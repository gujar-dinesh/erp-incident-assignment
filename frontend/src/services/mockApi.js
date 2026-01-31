// Mock API service for frontend-only development
// Returns mock data that matches the backend API structure

const MOCK_INCIDENTS = [
  {
    id: '1',
    title: 'Invoices Stuck in Processing Queue',
    description: 'All AP invoices are stuck in the processing queue and cannot be processed. The system shows error messages when attempting to process any invoice. This is blocking all payment operations.',
    erp_module: 'AP',
    environment: 'Prod',
    business_unit: 'Finance',
    severity: 'P1',
    category: 'Data Issue',
    status: 'open',
    created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    summary: 'Invoices Stuck in Processing Queue: All AP invoices are stuck in the processing queue',
    suggested_action: 'Immediate escalation required. Contact on-call engineer.'
  },
  {
    id: '2',
    title: 'API Integration Failure with External System',
    description: 'The external API connection is failing and data synchronization is broken. Error logs show connection timeouts when trying to sync invoice data.',
    erp_module: 'AP',
    environment: 'Prod',
    business_unit: 'Finance',
    severity: 'P1',
    category: 'Integration Failure',
    status: 'in_progress',
    created_at: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
    summary: 'API Integration Failure with External System: The external API connection is failing',
    suggested_action: 'Check integration logs and verify external system connectivity.'
  },
  {
    id: '3',
    title: 'Slow Performance in General Ledger Reports',
    description: 'System is running slow with delayed response times when generating GL reports. Users report waiting 5-10 minutes for reports that used to generate in seconds.',
    erp_module: 'GL',
    environment: 'Prod',
    business_unit: 'Finance',
    severity: 'P2',
    category: 'Configuration Issue',
    status: 'open',
    created_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
    summary: 'Slow Performance in General Ledger Reports: System is running slow',
    suggested_action: 'Review system configuration settings and compare with baseline.'
  },
  {
    id: '4',
    title: 'User Access Denied Error',
    description: 'Multiple users in the HR department cannot access the payroll module. They receive access denied errors even though their permissions were configured correctly last week.',
    erp_module: 'HR',
    environment: 'Prod',
    business_unit: 'HR',
    severity: 'P2',
    category: 'Security / Access',
    status: 'resolved',
    created_at: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
    summary: 'User Access Denied Error: Multiple users in the HR department cannot access',
    suggested_action: 'Review user permissions and verify access configuration.'
  },
  {
    id: '5',
    title: 'Duplicate Records in Inventory Module',
    description: 'Found duplicate inventory records for the same items. This is causing discrepancies in stock counts and affecting order processing accuracy.',
    erp_module: 'Inventory',
    environment: 'Test',
    business_unit: 'Operations',
    severity: 'P3',
    category: 'Data Issue',
    status: 'open',
    created_at: new Date(Date.now() - 12 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - 12 * 60 * 60 * 1000).toISOString(),
    summary: 'Duplicate Records in Inventory Module: Found duplicate inventory records',
    suggested_action: 'Investigate data integrity and verify transaction logs.'
  }
]

// Simulate network delay
const delay = (ms = 500) => new Promise(resolve => setTimeout(resolve, ms))

export const mockIncidentService = {
  async create(incidentData) {
    await delay(800)
    
    // Simulate enrichment logic
    const severity = incidentData.description.toLowerCase().includes('down') || 
                     incidentData.description.toLowerCase().includes('stuck') ||
                     incidentData.description.toLowerCase().includes('blocked')
                     ? 'P1' 
                     : incidentData.description.toLowerCase().includes('slow') ||
                       incidentData.description.toLowerCase().includes('delay')
                     ? 'P2'
                     : 'P3'
    
    const category = incidentData.description.toLowerCase().includes('api') ||
                     incidentData.description.toLowerCase().includes('integration')
                     ? 'Integration Failure'
                     : incidentData.description.toLowerCase().includes('access') ||
                       incidentData.description.toLowerCase().includes('permission')
                     ? 'Security / Access'
                     : incidentData.description.toLowerCase().includes('data') ||
                       incidentData.description.toLowerCase().includes('duplicate')
                     ? 'Data Issue'
                     : incidentData.description.toLowerCase().includes('config')
                     ? 'Configuration Issue'
                     : 'Unknown'
    
    const newIncident = {
      id: String(MOCK_INCIDENTS.length + 1),
      ...incidentData,
      severity,
      category,
      status: 'open',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      summary: `${incidentData.title}: ${incidentData.description.split('.')[0]}`,
      suggested_action: severity === 'P1' 
        ? 'Immediate escalation required. Contact on-call engineer.'
        : category === 'Integration Failure'
        ? 'Check integration logs and verify external system connectivity.'
        : 'Review incident details and assign to appropriate team.'
    }
    
    MOCK_INCIDENTS.unshift(newIncident)
    return newIncident
  },

  async getAll(params = {}) {
    await delay(600)
    
    let filtered = [...MOCK_INCIDENTS]
    
    // Apply filters
    if (params.status) {
      filtered = filtered.filter(inc => inc.status === params.status)
    }
    if (params.severity) {
      filtered = filtered.filter(inc => inc.severity === params.severity)
    }
    if (params.erp_module) {
      filtered = filtered.filter(inc => inc.erp_module === params.erp_module)
    }
    
    // Sort by created_at descending
    filtered.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
    
    // Pagination
    const limit = params.limit || 50
    let startIdx = 0
    
    if (params.next_token) {
      try {
        const decoded = JSON.parse(atob(params.next_token))
        const lastId = decoded.id
        startIdx = filtered.findIndex(inc => inc.id === lastId) + 1
      } catch (e) {
        // Invalid token, start from beginning
      }
    }
    
    const page = filtered.slice(startIdx, startIdx + limit)
    const nextToken = startIdx + limit < filtered.length 
      ? btoa(JSON.stringify({ id: page[page.length - 1].id }))
      : null
    
    return {
      incidents: page,
      next_token: nextToken
    }
  },

  async getById(id) {
    await delay(400)
    const incident = MOCK_INCIDENTS.find(inc => inc.id === id)
    if (!incident) {
      throw new Error('Incident not found')
    }
    return incident
  },

  async update(id, updateData) {
    await delay(500)
    const index = MOCK_INCIDENTS.findIndex(inc => inc.id === id)
    if (index === -1) {
      throw new Error('Incident not found')
    }
    
    const updated = {
      ...MOCK_INCIDENTS[index],
      ...updateData,
      updated_at: new Date().toISOString()
    }
    
    MOCK_INCIDENTS[index] = updated
    return updated
  }
}

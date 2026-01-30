from datetime import datetime
from typing import List, Optional, Dict, Tuple, Any
from app.models.incident import IncidentResponse, IncidentStatus, Severity, Category


class MockIncidentRepository:
    """
    In-memory repository for development/testing without DynamoDB.
    Uses a simple dictionary to store incidents.
    """
    
    def __init__(self):
        self._storage: Dict[str, dict] = {}
    
    def create(self, incident_data: dict) -> IncidentResponse:
        """Create a new incident in memory."""
        incident_id = incident_data['id']
        self._storage[incident_id] = incident_data.copy()
        return self._dict_to_response(incident_data)
    
    def get_by_id(self, incident_id: str) -> Optional[IncidentResponse]:
        """Retrieve an incident by ID."""
        if incident_id in self._storage:
            return self._dict_to_response(self._storage[incident_id])
        return None
    
    def list_all(
        self,
        limit: int = 50,
        last_key: Optional[Dict[str, Any]] = None,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        erp_module: Optional[str] = None
    ) -> Tuple[List[IncidentResponse], Optional[Dict[str, Any]]]:
        """
        List incidents with pagination and filtering support.
        Mock implementation matches real repository interface.
        """
        # Get all incidents
        all_incidents = [self._dict_to_response(item) for item in self._storage.values()]
        
        # Apply filters
        filtered = all_incidents
        if status:
            filtered = [inc for inc in filtered if inc.status.value == status]
        if severity:
            filtered = [inc for inc in filtered if inc.severity.value == severity]
        if erp_module:
            filtered = [inc for inc in filtered if inc.erp_module == erp_module]
        
        # Sort by created_at descending
        filtered.sort(key=lambda x: x.created_at, reverse=True)
        
        # Handle pagination
        start_idx = 0
        if last_key and 'id' in last_key:
            # Find the index of the last key
            for idx, inc in enumerate(filtered):
                if inc.id == last_key['id']:
                    start_idx = idx + 1
                    break
        
        # Get page of results
        end_idx = start_idx + limit
        page_incidents = filtered[start_idx:end_idx]
        
        # Determine next key
        next_key = None
        if end_idx < len(filtered):
            next_key = {'id': page_incidents[-1].id}
        
        return page_incidents, next_key
    
    def update(self, incident_id: str, update_data: dict) -> Optional[IncidentResponse]:
        """Update an existing incident."""
        if incident_id not in self._storage:
            return None
        
        item = self._storage[incident_id]
        for key, value in update_data.items():
            if key != 'id':
                item[key] = value
        
        # Always update updated_at
        item['updated_at'] = datetime.utcnow().isoformat()
        
        return self._dict_to_response(item)
    
    def _dict_to_response(self, item: dict) -> IncidentResponse:
        """Convert dictionary to IncidentResponse model."""
        return IncidentResponse(
            id=item['id'],
            title=item['title'],
            description=item['description'],
            erp_module=item['erp_module'],
            environment=item['environment'],
            business_unit=item['business_unit'],
            severity=Severity(item['severity']),
            category=Category(item['category']),
            status=IncidentStatus(item['status']),
            created_at=datetime.fromisoformat(item['created_at']),
            updated_at=datetime.fromisoformat(item['updated_at']),
            summary=item.get('summary'),
            suggested_action=item.get('suggested_action')
        )
    
    def clear(self):
        """Clear all stored incidents (useful for testing)."""
        self._storage.clear()

import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Query, Request
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.models.incident import IncidentCreate, IncidentUpdate, IncidentResponse, IncidentStatus, Severity, ERPModule
from app.repositories.incident_repository import IncidentRepository
from app.repositories.mock_incident_repository import MockIncidentRepository
from app.repositories.vector_repository import InMemoryVectorRepository
from app.services.enrichment_service import EnrichmentService
from app.services.rag_enrichment_service import RAGEnrichmentService
from app.services.embedding_service import EmbeddingService
from app.config import settings

router = APIRouter(prefix="/api/incidents", tags=["incidents"])

# Rate limiter - will be bound from app state in main.py
# For now, create instance that will be replaced
limiter = Limiter(key_func=get_remote_address)

# Use mock repository if explicitly set or if no AWS credentials in dev mode
use_mock_storage = (
    settings.use_mock or 
    (settings.environment == "development" and not settings.aws_access_key_id)
)

if use_mock_storage:
    repository = MockIncidentRepository()
    print("Using MOCK storage (in-memory)")
else:
    repository = IncidentRepository()
    print("Using REAL DynamoDB storage")

# Initialize enrichment service (RAG or rule-based)
if settings.use_rag:
    try:
        vector_repo = InMemoryVectorRepository(repository)
        enrichment_service = RAGEnrichmentService(vector_repo)
        print("Using RAG-enhanced enrichment service")
    except Exception as e:
        print(f"Failed to initialize RAG service: {e}. Falling back to rule-based.")
        enrichment_service = EnrichmentService()
else:
    enrichment_service = EnrichmentService()
    print("Using rule-based enrichment service")


@router.post("", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
async def create_incident(request: Request, incident: IncidentCreate) -> IncidentResponse:
    """
    Create a new ERP incident with automatic enrichment.
    Rate limited to 20 requests per minute per IP.
    
    The incident will be automatically enriched with:
    - Severity (P1, P2, or P3)
    - Category (Configuration Issue, Data Issue, etc.)
    - Summary
    - Suggested action
    
    If RAG is enabled, the system will:
    - Use rule-based enrichment for most cases (fast)
    - Use RAG with similar incidents for ambiguous cases
    - Learn from historical resolved incidents
    """
    try:
        # Enrich incident (uses RAG if enabled, otherwise rule-based)
        if isinstance(enrichment_service, RAGEnrichmentService):
            enrichment_result = enrichment_service.enrich_incident(incident)
            severity = enrichment_result['severity']
            category = enrichment_result['category']
            summary = enrichment_result['summary']
            suggested_action = enrichment_result['suggested_action']
            enrichment_method = enrichment_result.get('enrichment_method', 'rule_based')
        else:
            # Fallback to rule-based
            severity = enrichment_service.determine_severity(incident)
            category = enrichment_service.determine_category(incident)
            summary = enrichment_service.generate_summary(incident)
            suggested_action = enrichment_service.suggest_action(incident, category, severity)
            enrichment_method = 'rule_based'
        
        # Prepare data for storage
        incident_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        incident_data = {
            'id': incident_id,
            'title': incident.title,
            'description': incident.description,
            'erp_module': incident.erp_module.value,
            'environment': incident.environment.value,
            'business_unit': incident.business_unit,
            'severity': severity.value,
            'category': category.value,
            'status': 'open',
            'created_at': now,
            'updated_at': now,
            'summary': summary,
            'suggested_action': suggested_action
        }
        
        # Save to database
        created_incident = repository.create(incident_data)
        
        # If RAG is enabled, generate and store embedding for future similarity search
        if settings.use_rag and isinstance(enrichment_service, RAGEnrichmentService):
            try:
                embedding_service = EmbeddingService()
                embedding = embedding_service.generate_incident_embedding(
                    incident.title,
                    incident.description
                )
                # Store embedding in vector repository
                vector_repo = enrichment_service.vector_repo
                vector_repo.add_embedding(
                    incident_id,
                    embedding,
                    metadata={
                        'status': 'open',
                        'created_at': now,
                        'category': category.value,
                        'severity': severity.value
                    }
                )
            except Exception as e:
                # Don't fail incident creation if embedding fails
                print(f"Warning: Failed to store embedding for incident {incident_id}: {e}")
        
        return created_incident
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create incident: {str(e)}"
        )


class IncidentListResponse(BaseModel):
    incidents: List[IncidentResponse]
    next_token: Optional[str] = None
    total_count: Optional[int] = None


@router.get("", response_model=IncidentListResponse)
@limiter.limit("100/minute")
async def list_incidents(
    request: Request,
    limit: int = Query(50, ge=1, le=100, description="Number of incidents to return"),
    next_token: Optional[str] = Query(None, description="Pagination token from previous request"),
    status: Optional[str] = Query(None, description="Filter by status (or 'all' for all statuses)"),
    severity: Optional[Severity] = Query(None, description="Filter by severity"),
    erp_module: Optional[ERPModule] = Query(None, description="Filter by ERP module")
) -> IncidentListResponse:
    """
    Retrieve incidents with pagination and filtering support.
    Rate limited to 100 requests per minute per IP.
    
    Uses efficient DynamoDB queries with GSI when filters are provided.
    Returns paginated results with next_token for subsequent requests.
    
    **Recommended**: Always provide status filter for best performance.
    """
    try:
        # Decode pagination token (simple base64 encoding in production)
        last_key = None
        if next_token:
            import json
            import base64
            try:
                decoded = base64.b64decode(next_token).decode('utf-8')
                last_key = json.loads(decoded)
            except:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid pagination token"
                )
        
        # Handle status filter - support 'all' to explicitly request all statuses
        explicitly_all_statuses = False
        if status == 'all':
            status_str = None  # Explicitly request all statuses
            explicitly_all_statuses = True
        elif status:
            # Validate status enum if provided
            try:
                status_enum = IncidentStatus(status)
                status_str = status_enum.value
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status value: {status}"
                )
        else:
            status_str = None
        
        severity_str = severity.value if severity else None
        module_str = erp_module.value if erp_module else None
        
        # Default to 'open' status only if NO filters are provided at all AND user didn't explicitly request 'all'
        # This provides a sensible default for initial page load
        if status_str is None and not explicitly_all_statuses and not severity_str and not module_str:
            status_str = 'open'  # Default to open incidents for efficiency when no filters
        
        incidents, next_key = repository.list_all(
            limit=limit,
            last_key=last_key,
            status=status_str,
            severity=severity_str,
            erp_module=module_str
        )
        
        # Encode next key for pagination token
        next_token_str = None
        if next_key:
            import json
            import base64
            encoded = base64.b64encode(json.dumps(next_key).encode('utf-8')).decode('utf-8')
            next_token_str = encoded
        
        return IncidentListResponse(
            incidents=incidents,
            next_token=next_token_str
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve incidents: {str(e)}"
        )


@router.get("/{incident_id}", response_model=IncidentResponse)
@limiter.limit("200/minute")
async def get_incident(request: Request, incident_id: str) -> IncidentResponse:
    """
    Retrieve a specific incident by ID.
    Rate limited to 200 requests per minute per IP.
    """
    try:
        incident = repository.get_by_id(incident_id)
        if not incident:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Incident with id {incident_id} not found"
            )
        return incident
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve incident: {str(e)}"
        )


@router.patch("/{incident_id}", response_model=IncidentResponse)
@limiter.limit("50/minute")
async def update_incident(request: Request, incident_id: str, update: IncidentUpdate) -> IncidentResponse:
    """
    Update an incident. Currently supports updating status, title, and description.
    Rate limited to 50 requests per minute per IP.
    """
    try:
        # Build update dictionary
        update_data = {}
        if update.status:
            update_data['status'] = update.status.value
        if update.title:
            update_data['title'] = update.title
        if update.description:
            update_data['description'] = update.description
        
        if not update_data:
            # No fields to update, return current incident
            incident = repository.get_by_id(incident_id)
            if not incident:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Incident with id {incident_id} not found"
                )
            return incident
        
        # Perform update
        updated_incident = repository.update(incident_id, update_data)
        if not updated_incident:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Incident with id {incident_id} not found"
            )
        
        return updated_incident
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update incident: {str(e)}"
        )


@router.get("/{incident_id}/similar", response_model=List[IncidentResponse])
@limiter.limit("50/minute")
async def get_similar_incidents(
    request: Request,
    incident_id: str,
    limit: int = Query(5, ge=1, le=10, description="Number of similar incidents to return")
) -> List[IncidentResponse]:
    """
    Get similar incidents to a given incident.
    Only available when RAG is enabled.
    
    Returns incidents that are semantically similar based on vector embeddings.
    Useful for finding related incidents and learning from past resolutions.
    """
    if not settings.use_rag or not isinstance(enrichment_service, RAGEnrichmentService):
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="RAG feature is not enabled. Set USE_RAG=true in your .env file."
        )
    
    try:
        # Get the incident
        incident = repository.get_by_id(incident_id)
        if not incident:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Incident with id {incident_id} not found"
            )
        
        # Get embedding for this incident
        vector_repo = enrichment_service.vector_repo
        embedding = vector_repo.get_embedding(incident_id)
        
        if not embedding:
            # Generate embedding if not stored
            embedding_service = EmbeddingService()
            embedding = embedding_service.generate_incident_embedding(
                incident.title,
                incident.description
            )
            # Store it for future use
            vector_repo.add_embedding(
                incident_id,
                embedding,
                metadata={
                    'status': incident.status.value,
                    'created_at': incident.created_at.isoformat(),
                    'category': incident.category.value,
                    'severity': incident.severity.value
                }
            )
        
        # Find similar incidents
        similar = vector_repo.find_similar(
            embedding,
            limit=limit,
            filters={"status": "resolved"}  # Only show resolved incidents
        )
        
        # Return just the incidents (without similarity scores)
        return [inc for inc, score in similar]
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to find similar incidents: {str(e)}"
        )

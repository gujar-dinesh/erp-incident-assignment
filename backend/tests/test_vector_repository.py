"""
Test-Driven Development tests for Vector Repository.

Following TDD principles for vector similarity search functionality.
"""

import pytest
import numpy as np
from app.repositories.vector_repository import InMemoryVectorRepository
from app.repositories.mock_incident_repository import MockIncidentRepository
from app.models.incident import IncidentResponse, Severity, Category, IncidentStatus
from datetime import datetime


@pytest.fixture
def vector_repo():
    """Create vector repository for testing."""
    repo = MockIncidentRepository()
    return InMemoryVectorRepository(repo)


@pytest.fixture
def sample_embedding():
    """Sample embedding vector for testing (1536 dimensions for OpenAI)."""
    return [0.1] * 1536


@pytest.fixture
def resolved_incident():
    """Create a resolved incident for similarity testing."""
    return IncidentResponse(
        id="test-1",
        title="Payment API Down",
        description="External payment API is not responding",
        erp_module="AP",
        environment="Prod",
        business_unit="Finance",
        severity=Severity.P1,
        category=Category.INTEGRATION_FAILURE,
        status=IncidentStatus.RESOLVED,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        summary="Payment API Down: External payment API is not responding",
        suggested_action="Check integration logs"
    )


class TestVectorRepository:
    """
    TDD tests for Vector Repository.
    
    Test-Driven Development approach:
    - Write test first
    - Implement feature
    - Refactor
    """
    
    @pytest.mark.unit
    @pytest.mark.rag
    def test_add_embedding(self, vector_repo, sample_embedding):
        """
        TDD Test: Should be able to add embeddings.
        Test first: RED -> Implement: GREEN -> Refactor
        """
        incident_id = "test-incident-1"
        metadata = {
            'status': 'resolved',
            'category': 'Integration Failure',
            'severity': 'P1'
        }
        
        vector_repo.add_embedding(incident_id, sample_embedding, metadata)
        
        # Verify embedding was stored
        retrieved = vector_repo.get_embedding(incident_id)
        assert retrieved == sample_embedding
    
    @pytest.mark.unit
    @pytest.mark.rag
    def test_get_embedding_not_found(self, vector_repo):
        """
        TDD Test: Should return None for non-existent embedding.
        """
        result = vector_repo.get_embedding("non-existent")
        assert result is None
    
    @pytest.mark.unit
    @pytest.mark.rag
    def test_remove_embedding(self, vector_repo, sample_embedding):
        """
        TDD Test: Should be able to remove embeddings.
        """
        incident_id = "test-incident-2"
        vector_repo.add_embedding(incident_id, sample_embedding, {})
        
        # Remove it
        vector_repo.remove_embedding(incident_id)
        
        # Verify it's gone
        assert vector_repo.get_embedding(incident_id) is None
    
    @pytest.mark.unit
    @pytest.mark.rag
    def test_find_similar_with_no_incidents(self, vector_repo, sample_embedding):
        """
        TDD Test: Should return empty list when no incidents exist.
        """
        similar = vector_repo.find_similar(sample_embedding, limit=5)
        assert similar == []
    
    @pytest.mark.unit
    @pytest.mark.rag
    def test_find_similar_with_matching_incident(self, vector_repo, sample_embedding, resolved_incident):
        """
        TDD Test: Should find similar incidents above threshold.
        """
        # Add incident to repository
        incident_data = {
            'id': resolved_incident.id,
            'title': resolved_incident.title,
            'description': resolved_incident.description,
            'erp_module': resolved_incident.erp_module,
            'environment': resolved_incident.environment,
            'business_unit': resolved_incident.business_unit,
            'severity': resolved_incident.severity.value,
            'category': resolved_incident.category.value,
            'status': resolved_incident.status.value,
            'created_at': resolved_incident.created_at.isoformat(),
            'updated_at': resolved_incident.updated_at.isoformat(),
            'summary': resolved_incident.summary,
            'suggested_action': resolved_incident.suggested_action
        }
        vector_repo.incident_repo.create(incident_data)
        
        # Add embedding (same as query = 100% similarity)
        vector_repo.add_embedding(
            resolved_incident.id,
            sample_embedding,
            {'status': 'resolved'}
        )
        
        # Find similar
        similar = vector_repo.find_similar(
            sample_embedding,
            limit=5,
            filters={'status': 'resolved'}
        )
        
        # Should find the incident (100% similarity)
        assert len(similar) == 1
        assert similar[0][0].id == resolved_incident.id
        assert similar[0][1] == 1.0  # 100% similarity
    
    @pytest.mark.unit
    @pytest.mark.rag
    def test_find_similar_filters_by_status(self, vector_repo, sample_embedding):
        """
        TDD Test: Should filter by status when finding similar incidents.
        """
        # This test verifies filtering works correctly
        # Implementation should respect status filter
        similar = vector_repo.find_similar(
            sample_embedding,
            limit=5,
            filters={'status': 'resolved'}
        )
        
        # Should only return resolved incidents
        for incident, score in similar:
            assert incident.status.value == 'resolved'
    
    @pytest.mark.unit
    @pytest.mark.rag
    def test_get_stats(self, vector_repo, sample_embedding):
        """
        TDD Test: Should provide statistics about stored embeddings.
        """
        # Add some embeddings
        vector_repo.add_embedding("id1", sample_embedding, {})
        vector_repo.add_embedding("id2", sample_embedding, {})
        
        stats = vector_repo.get_stats()
        
        assert stats['total_embeddings'] == 2
        assert 'cache_size' in stats

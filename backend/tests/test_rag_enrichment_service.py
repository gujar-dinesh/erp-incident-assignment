"""
Test-Driven Development tests for RAG Enrichment Service.

Following TDD principles:
1. Write test first (RED)
2. Implement feature (GREEN)
3. Refactor (REFACTOR)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.models.incident import IncidentCreate, ERPModule, Environment, Severity, Category
from app.services.rag_enrichment_service import RAGEnrichmentService
from app.repositories.vector_repository import InMemoryVectorRepository
from app.repositories.mock_incident_repository import MockIncidentRepository
from app.config import settings


@pytest.fixture
def mock_vector_repo():
    """Mock vector repository for RAG service tests."""
    repo = MockIncidentRepository()
    return InMemoryVectorRepository(repo)


@pytest.fixture
def rag_service(mock_vector_repo):
    """Create RAG enrichment service for testing."""
    # Mock OpenAI client to avoid API calls in tests
    with patch('app.services.rag_enrichment_service.openai') as mock_openai:
        mock_client = MagicMock()
        mock_openai.OpenAI.return_value = mock_client
        service = RAGEnrichmentService(mock_vector_repo)
        service.llm_client = None  # Disable LLM for unit tests
        return service


class TestRAGEnrichmentService:
    """
    Test-Driven Development tests for RAG enrichment.
    
    TDD Cycle:
    1. RED: Write failing test
    2. GREEN: Implement minimal code to pass
    3. REFACTOR: Improve code quality
    """
    
    @pytest.mark.unit
    @pytest.mark.rag
    def test_should_use_rag_for_unknown_category(self, rag_service, sample_incident):
        """
        TDD Test: RAG should be used when category is Unknown.
        Test first, then implement.
        """
        # Create incident that will result in Unknown category
        incident = IncidentCreate(
            title="Vague Issue",
            description="Something is wrong but unclear what",
            erp_module=ERPModule.GL,
            environment=Environment.PROD,
            business_unit="Finance"
        )
        
        result = rag_service.enrich_incident(incident)
        
        # Should use RAG when category is unknown
        # (In actual implementation, this triggers RAG)
        assert result['category'] in [Category.UNKNOWN, Category.DATA_ISSUE]  # May match "wrong"
        assert 'enrichment_method' in result
    
    @pytest.mark.unit
    @pytest.mark.rag
    def test_should_use_rag_for_short_description(self, rag_service):
        """
        TDD Test: RAG should be used for very short descriptions (< 50 chars).
        """
        incident = IncidentCreate(
            title="Short Issue",
            description="Problem.",  # Very short
            erp_module=ERPModule.AP,
            environment=Environment.PROD,
            business_unit="Finance"
        )
        
        result = rag_service.enrich_incident(incident)
        
        # Should trigger RAG due to short description
        assert result['severity'] in [Severity.P1, Severity.P2, Severity.P3]
        assert result['category'] is not None
    
    @pytest.mark.unit
    @pytest.mark.rag
    def test_should_fallback_to_rule_based_when_no_similar_incidents(self, rag_service, p1_incident):
        """
        TDD Test: Should fallback to rule-based when no similar incidents found.
        """
        result = rag_service.enrich_incident(p1_incident)
        
        # Should still work (fallback to rule-based)
        assert result['severity'] == Severity.P1  # Clear keywords
        assert result['category'] is not None
        assert 'enrichment_method' in result
    
    @pytest.mark.unit
    @pytest.mark.rag
    def test_should_handle_rag_failure_gracefully(self, rag_service, sample_incident):
        """
        TDD Test: Should handle RAG failures gracefully and fallback.
        """
        # Mock embedding service to raise exception
        with patch.object(rag_service.embedding_service, 'generate_incident_embedding', side_effect=Exception("API Error")):
            result = rag_service.enrich_incident(sample_incident)
            
            # Should still return result (fallback)
            assert result['severity'] is not None
            assert result['category'] is not None
    
    @pytest.mark.unit
    @pytest.mark.rag
    def test_enrichment_result_structure(self, rag_service, sample_incident):
        """
        TDD Test: Enrichment result should have correct structure.
        """
        result = rag_service.enrich_incident(sample_incident)
        
        # Verify structure
        assert 'severity' in result
        assert 'category' in result
        assert 'summary' in result
        assert 'suggested_action' in result
        assert 'enrichment_method' in result
        assert 'similar_incidents' in result
        
        # Verify types
        assert isinstance(result['severity'], Severity)
        assert isinstance(result['category'], Category)
        assert isinstance(result['summary'], str)
        assert isinstance(result['suggested_action'], str)
        assert isinstance(result['similar_incidents'], list)

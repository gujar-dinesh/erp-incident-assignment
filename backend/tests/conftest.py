"""
Test configuration and fixtures for TDD approach.

This file contains shared fixtures used across all test modules,
following Test-Driven Development principles.
"""

import pytest
from moto import mock_dynamodb
import boto3
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
from app.models.incident import IncidentCreate, ERPModule, Environment
from app.repositories.mock_incident_repository import MockIncidentRepository
from app.services.enrichment_service import EnrichmentService
from app.services.rag_enrichment_service import RAGEnrichmentService
from app.repositories.vector_repository import InMemoryVectorRepository


@pytest.fixture
def dynamodb_table():
    """
    Create a mock DynamoDB table for integration tests.
    Uses moto to mock AWS DynamoDB without real AWS calls.
    """
    with mock_dynamodb():
        dynamodb = boto3.resource('dynamodb', region_name=settings.aws_region)
        table = dynamodb.create_table(
            TableName=settings.dynamodb_table_name,
            KeySchema=[
                {'AttributeName': 'id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        yield table


@pytest.fixture
def api_client():
    """
    Create a test client for FastAPI endpoints.
    Used for integration tests of API routes.
    """
    return TestClient(app)


@pytest.fixture
def mock_repository():
    """
    Create a mock in-memory repository for unit tests.
    Faster than DynamoDB and doesn't require AWS mocking.
    """
    return MockIncidentRepository()


@pytest.fixture
def enrichment_service():
    """
    Create an enrichment service instance for unit tests.
    Uses rule-based service (no RAG dependencies).
    """
    return EnrichmentService()


@pytest.fixture
def sample_incident():
    """
    Create a sample incident for testing.
    Standard test data used across multiple tests.
    """
    return IncidentCreate(
        title="Test Incident",
        description="This is a test incident for TDD",
        erp_module=ERPModule.AP,
        environment=Environment.PROD,
        business_unit="Finance"
    )


@pytest.fixture
def p1_incident():
    """Sample P1 (critical) incident for severity testing."""
    return IncidentCreate(
        title="System Down",
        description="Production system is completely down and all users are affected",
        erp_module=ERPModule.AP,
        environment=Environment.PROD,
        business_unit="Finance"
    )


@pytest.fixture
def p2_incident():
    """Sample P2 (medium) incident for severity testing."""
    return IncidentCreate(
        title="Slow Performance",
        description="System is running slow with delayed response times",
        erp_module=ERPModule.GL,
        environment=Environment.PROD,
        business_unit="Finance"
    )


@pytest.fixture
def integration_incident():
    """Sample incident for integration failure category testing."""
    return IncidentCreate(
        title="API Integration Failure",
        description="External API connection is failing and cannot sync data",
        erp_module=ERPModule.AR,
        environment=Environment.PROD,
        business_unit="Sales"
    )

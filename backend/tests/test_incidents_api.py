"""
Test-Driven Development integration tests for API endpoints.

Following TDD approach:
- Tests written to define API contract
- Implementation follows test requirements
- Tests verify end-to-end functionality
"""

import pytest
from moto import mock_dynamodb
import boto3
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
from app.models.incident import ERPModule, Environment, IncidentStatus


@pytest.fixture
def dynamodb_table():
    """
    TDD Fixture: Mock DynamoDB table for integration tests.
    Uses moto to avoid real AWS calls during testing.
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
def client():
    """
    TDD Fixture: FastAPI test client.
    Provides isolated test environment for API endpoints.
    """
    return TestClient(app)


class TestIncidentsAPI:
    """
    TDD Integration Tests for Incident API Endpoints.
    
    These tests verify the complete API contract:
    - Request/response formats
    - Status codes
    - Data validation
    - Error handling
    """
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_create_incident(self, client, dynamodb_table):
        """
        TDD Integration Test: Create incident endpoint.
        Requirement: POST /api/incidents creates incident with enrichment
        """
        payload = {
            "title": "Test Incident",
            "description": "This is a test incident description",
            "erp_module": "AP",
            "environment": "Prod",
            "business_unit": "Finance"
        }
        response = client.post("/api/incidents", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == payload["title"]
        assert data["severity"] in ["P1", "P2", "P3"]
        assert data["category"] is not None
        assert data["status"] == "open"
        assert "id" in data
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_create_incident_validation_error(self, client):
        """
        TDD Test: Input validation for incident creation.
        Requirement: Empty title should return 422 validation error
        """
        payload = {
            "title": "",  # Empty title should fail
            "description": "Test",
            "erp_module": "AP",
            "environment": "Prod",
            "business_unit": "Finance"
        }
        response = client.post("/api/incidents", json=payload)
        assert response.status_code == 422
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_list_incidents(self, client, dynamodb_table):
        """
        TDD Integration Test: List incidents endpoint.
        Requirement: GET /api/incidents returns list of incidents
        """
        # Create a test incident first
        payload = {
            "title": "Test Incident",
            "description": "Test description",
            "erp_module": "AP",
            "environment": "Prod",
            "business_unit": "Finance"
        }
        client.post("/api/incidents", json=payload)
        
        # List incidents
        response = client.get("/api/incidents")
        assert response.status_code == 200
        data = response.json()
        assert "incidents" in data
        assert isinstance(data["incidents"], list)
        assert len(data["incidents"]) >= 1
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_get_incident_by_id(self, client, dynamodb_table):
        """
        TDD Integration Test: Get incident by ID.
        Requirement: GET /api/incidents/{id} returns specific incident
        """
        # Create an incident
        payload = {
            "title": "Test Incident",
            "description": "Test description",
            "erp_module": "AP",
            "environment": "Prod",
            "business_unit": "Finance"
        }
        create_response = client.post("/api/incidents", json=payload)
        incident_id = create_response.json()["id"]
        
        # Get the incident
        response = client.get(f"/api/incidents/{incident_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == incident_id
        assert data["title"] == payload["title"]
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_get_incident_not_found(self, client, dynamodb_table):
        """
        TDD Test: 404 error for non-existent incident.
        Requirement: GET /api/incidents/{id} returns 404 if not found
        """
        response = client.get("/api/incidents/non-existent-id")
        assert response.status_code == 404
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_update_incident_status(self, client, dynamodb_table):
        """
        TDD Integration Test: Update incident status.
        Requirement: PATCH /api/incidents/{id} updates status
        """
        # Create an incident
        payload = {
            "title": "Test Incident",
            "description": "Test description",
            "erp_module": "AP",
            "environment": "Prod",
            "business_unit": "Finance"
        }
        create_response = client.post("/api/incidents", json=payload)
        incident_id = create_response.json()["id"]
        
        # Update status
        update_payload = {"status": "in_progress"}
        response = client.patch(f"/api/incidents/{incident_id}", json=update_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "in_progress"
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_update_incident_not_found(self, client, dynamodb_table):
        """
        TDD Test: 404 error when updating non-existent incident.
        Requirement: PATCH /api/incidents/{id} returns 404 if not found
        """
        update_payload = {"status": "resolved"}
        response = client.patch("/api/incidents/non-existent-id", json=update_payload)
        assert response.status_code == 404
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_root_endpoint(self, client):
        """
        TDD Test: Root endpoint returns API info.
        Requirement: GET / returns API metadata
        """
        response = client.get("/")
        assert response.status_code == 200
        assert "message" in response.json()
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_health_check(self, client):
        """
        TDD Test: Health check endpoint.
        Requirement: GET /health returns healthy status
        """
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

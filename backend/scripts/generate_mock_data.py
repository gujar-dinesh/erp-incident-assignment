"""
Script to generate mock incident data for testing RAG functionality.

This script creates a variety of incidents with different:
- Categories (Configuration, Data, Integration, Security)
- Severities (P1, P2, P3)
- Statuses (open, resolved, closed)
- ERP Modules

Run this script to populate your database with test data.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import uuid
from datetime import datetime, timedelta
from app.repositories.incident_repository import IncidentRepository
from app.repositories.mock_incident_repository import MockIncidentRepository
from app.services.embedding_service import EmbeddingService
from app.repositories.vector_repository import InMemoryVectorRepository
from app.config import settings

# Mock incident templates
MOCK_INCIDENTS = [
    # Integration Failures
    {
        "title": "Payment API Integration Failure",
        "description": "The external payment API is completely down and cannot process any transactions. All users are affected and cannot complete purchases. Error logs show connection timeouts when trying to sync invoice data.",
        "erp_module": "AP",
        "environment": "Prod",
        "business_unit": "Finance",
        "severity": "P1",
        "category": "Integration Failure",
        "status": "resolved",
        "suggested_action": "Check integration logs and verify external system connectivity. Contact payment provider support."
    },
    {
        "title": "API Connection Timeout",
        "description": "Intermittent API connection timeouts when syncing data with external system. Some users experiencing delays in data synchronization.",
        "erp_module": "AR",
        "environment": "Prod",
        "business_unit": "Sales",
        "severity": "P2",
        "category": "Integration Failure",
        "status": "resolved",
        "suggested_action": "Check integration logs and verify external system connectivity. Review network configuration."
    },
    {
        "title": "Webhook Delivery Failure",
        "description": "Webhooks are failing to deliver to external systems. Some integrations are not receiving updates.",
        "erp_module": "GL",
        "environment": "Prod",
        "business_unit": "IT",
        "severity": "P2",
        "category": "Integration Failure",
        "status": "resolved",
        "suggested_action": "Check integration logs and verify external system connectivity. Review webhook configuration."
    },
    
    # Data Issues
    {
        "title": "Duplicate Invoice Records",
        "description": "Duplicate invoice records are being created in the system. Multiple invoices with same invoice number appearing in database.",
        "erp_module": "AP",
        "environment": "Prod",
        "business_unit": "Finance",
        "severity": "P2",
        "category": "Data Issue",
        "status": "resolved",
        "suggested_action": "Investigate data integrity and verify transaction logs. Check for duplicate processing."
    },
    {
        "title": "Missing Transaction Data",
        "description": "Some transaction records are missing from the general ledger. Data appears to be lost during processing.",
        "erp_module": "GL",
        "environment": "Prod",
        "business_unit": "Accounting",
        "severity": "P1",
        "category": "Data Issue",
        "status": "resolved",
        "suggested_action": "Investigate data integrity and verify transaction logs. Check database backup."
    },
    {
        "title": "Incorrect Data in Reports",
        "description": "Financial reports showing incorrect data. Numbers don't match expected values. Data appears to be corrupted.",
        "erp_module": "GL",
        "environment": "Prod",
        "business_unit": "Finance",
        "severity": "P2",
        "category": "Data Issue",
        "status": "resolved",
        "suggested_action": "Investigate data integrity and verify transaction logs. Review report generation logic."
    },
    
    # Security/Access Issues
    {
        "title": "User Cannot Access System",
        "description": "Multiple users reporting they cannot log in to the system. Getting access denied errors even with valid credentials.",
        "erp_module": "HR",
        "environment": "Prod",
        "business_unit": "HR",
        "severity": "P1",
        "category": "Security / Access",
        "status": "resolved",
        "suggested_action": "Review user permissions and verify access configuration. Check authentication service."
    },
    {
        "title": "Permission Denied for Reports",
        "description": "Users with valid access are getting permission denied errors when trying to generate reports. Some users affected.",
        "erp_module": "GL",
        "environment": "Prod",
        "business_unit": "Finance",
        "severity": "P2",
        "category": "Security / Access",
        "status": "resolved",
        "suggested_action": "Review user permissions and verify access configuration. Check role assignments."
    },
    {
        "title": "Password Reset Not Working",
        "description": "Password reset functionality is not working. Users cannot reset their passwords through the self-service portal.",
        "erp_module": "HR",
        "environment": "Prod",
        "business_unit": "IT",
        "severity": "P2",
        "category": "Security / Access",
        "status": "resolved",
        "suggested_action": "Review user permissions and verify access configuration. Check password reset service."
    },
    
    # Configuration Issues
    {
        "title": "Incorrect Tax Configuration",
        "description": "Tax calculation is incorrect due to wrong configuration settings. Tax rates are not matching expected values.",
        "erp_module": "AP",
        "environment": "Prod",
        "business_unit": "Finance",
        "severity": "P2",
        "category": "Configuration Issue",
        "status": "resolved",
        "suggested_action": "Review system configuration settings and compare with baseline. Update tax configuration."
    },
    {
        "title": "Misconfigured Approval Workflow",
        "description": "Approval workflow is not working correctly. Approvals are being routed to wrong users due to configuration error.",
        "erp_module": "AP",
        "environment": "Prod",
        "business_unit": "Finance",
        "severity": "P2",
        "category": "Configuration Issue",
        "status": "resolved",
        "suggested_action": "Review system configuration settings and compare with baseline. Fix workflow configuration."
    },
    {
        "title": "Wrong System Parameters",
        "description": "System parameters are set incorrectly causing calculation errors. Financial calculations are producing wrong results.",
        "erp_module": "GL",
        "environment": "Prod",
        "business_unit": "Accounting",
        "severity": "P1",
        "category": "Configuration Issue",
        "status": "resolved",
        "suggested_action": "Review system configuration settings and compare with baseline. Restore correct parameters."
    },
    
    # Performance Issues
    {
        "title": "Slow Report Generation",
        "description": "Report generation is very slow. Users waiting 10-15 minutes for reports that used to generate in seconds.",
        "erp_module": "GL",
        "environment": "Prod",
        "business_unit": "Finance",
        "severity": "P2",
        "category": "Unknown",
        "status": "resolved",
        "suggested_action": "Review incident details and assign to appropriate team. Check database performance."
    },
    {
        "title": "System Performance Degradation",
        "description": "System is running slow with delayed response times. Some users experiencing timeouts when accessing modules.",
        "erp_module": "Inventory",
        "environment": "Prod",
        "business_unit": "Operations",
        "severity": "P2",
        "category": "Unknown",
        "status": "resolved",
        "suggested_action": "Review incident details and assign to appropriate team. Check system resources."
    },
    
    # More variations for better testing
    {
        "title": "API Authentication Failure",
        "description": "External API authentication is failing. Cannot authenticate with third-party service.",
        "erp_module": "AR",
        "environment": "Prod",
        "business_unit": "Sales",
        "severity": "P1",
        "category": "Integration Failure",
        "status": "resolved",
        "suggested_action": "Check integration logs and verify external system connectivity. Review API credentials."
    },
    {
        "title": "Data Export Failing",
        "description": "Data export functionality is not working. Cannot export data to external systems.",
        "erp_module": "GL",
        "environment": "Prod",
        "business_unit": "Finance",
        "severity": "P2",
        "category": "Integration Failure",
        "status": "resolved",
        "suggested_action": "Check integration logs and verify external system connectivity. Review export configuration."
    },
]


def generate_mock_data(num_incidents: int = None, use_rag: bool = True):
    """
    Generate mock incident data.
    
    Args:
        num_incidents: Number of incidents to generate (None = use all templates)
        use_rag: Whether to generate embeddings for RAG
    """
    # Determine which repository to use
    if settings.use_mock or (settings.environment == "development" and not settings.aws_access_key_id):
        repo = MockIncidentRepository()
        print("Using MOCK repository")
    else:
        repo = IncidentRepository()
        print("Using REAL DynamoDB repository")
    
    # Initialize vector repository if RAG is enabled
    vector_repo = None
    embedding_service = None
    
    if use_rag and settings.use_rag and settings.openai_api_key:
        try:
            vector_repo = InMemoryVectorRepository(repo)
            embedding_service = EmbeddingService()
            print("RAG enabled - will generate embeddings")
        except Exception as e:
            print(f"Warning: Could not initialize RAG: {e}")
            print("   Continuing without embeddings...")
            use_rag = False
    else:
        if use_rag:
            print("RAG not enabled or OpenAI API key not set")
            print("   Set USE_RAG=true and OPENAI_API_KEY in .env to generate embeddings")
        use_rag = False
    
    # Select incidents to create
    incidents_to_create = MOCK_INCIDENTS
    if num_incidents:
        incidents_to_create = MOCK_INCIDENTS[:num_incidents]
    
    print(f"\nCreating {len(incidents_to_create)} mock incidents...\n")
    
    created_count = 0
    embedding_count = 0
    
    for i, incident_template in enumerate(incidents_to_create, 1):
        # Create incident with unique ID
        incident_id = str(uuid.uuid4())
        now = datetime.utcnow() - timedelta(days=len(incidents_to_create) - i)  # Stagger dates
        
        incident_data = {
            'id': incident_id,
            'title': incident_template['title'],
            'description': incident_template['description'],
            'erp_module': incident_template['erp_module'],
            'environment': incident_template['environment'],
            'business_unit': incident_template['business_unit'],
            'severity': incident_template['severity'],
            'category': incident_template['category'],
            'status': incident_template['status'],
            'created_at': now.isoformat(),
            'updated_at': now.isoformat(),
            'summary': f"{incident_template['title']}: {incident_template['description'][:100]}...",
            'suggested_action': incident_template['suggested_action']
        }
        
        # Create incident
        try:
            repo.create(incident_data)
            created_count += 1
            print(f"[{i}/{len(incidents_to_create)}] Created: {incident_template['title']}")
            
            # Generate and store embedding if RAG is enabled
            if use_rag and vector_repo and embedding_service:
                try:
                    embedding = embedding_service.generate_incident_embedding(
                        incident_template['title'],
                        incident_template['description']
                    )
                    vector_repo.add_embedding(
                        incident_id,
                        embedding,
                        metadata={
                            'status': incident_template['status'],
                            'created_at': now.isoformat(),
                            'category': incident_template['category'],
                            'severity': incident_template['severity']
                        }
                    )
                    embedding_count += 1
                except Exception as e:
                    print(f"   Failed to generate embedding: {e}")
        except Exception as e:
            print(f"[{i}/{len(incidents_to_create)}] Failed to create: {e}")
    
    print(f"\nSummary:")
    print(f"   Created {created_count} incidents")
    if use_rag:
        print(f"   Generated {embedding_count} embeddings")
    print(f"\nTip: Use these incidents to test RAG similarity search!")
    print(f"   Try creating a new incident similar to one of these and see if RAG finds it.")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate mock incident data for testing")
    parser.add_argument(
        "--count",
        type=int,
        default=None,
        help="Number of incidents to create (default: all templates)"
    )
    parser.add_argument(
        "--no-rag",
        action="store_true",
        help="Skip embedding generation (faster, but no RAG testing)"
    )
    
    args = parser.parse_args()
    
    generate_mock_data(
        num_incidents=args.count,
        use_rag=not args.no_rag
    )

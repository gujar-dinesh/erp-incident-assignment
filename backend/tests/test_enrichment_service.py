"""
Test-Driven Development tests for Enrichment Service.

Following TDD principles:
1. RED: Write failing test first
2. GREEN: Implement minimal code to pass
3. REFACTOR: Improve code quality

These tests were written BEFORE implementation to drive development.
"""

import pytest
from app.models.incident import IncidentCreate, ERPModule, Environment, Severity, Category
from app.services.enrichment_service import EnrichmentService


class TestEnrichmentService:
    """
    TDD Test Suite for Enrichment Service.
    
    Each test represents a requirement that was tested first,
    then implemented to make the test pass.
    """
    
    @pytest.mark.unit
    def test_determine_severity_p1_critical(self, p1_incident):
        """
        TDD Test: P1 severity for critical incidents.
        Requirement: System down = P1
        """
        assert EnrichmentService.determine_severity(p1_incident) == Severity.P1
    
    @pytest.mark.unit
    def test_determine_severity_p1_stuck(self):
        """
        TDD Test: P1 severity for stuck/blocked incidents.
        Requirement: Stuck/blocked = P1
        """
        incident = IncidentCreate(
            title="Invoices Stuck",
            description="All invoices are stuck in processing queue",
            erp_module=ERPModule.AP,
            environment=Environment.PROD,
            business_unit="Finance"
        )
        assert EnrichmentService.determine_severity(incident) == Severity.P1
    
    @pytest.mark.unit
    def test_determine_severity_p2_slow(self, p2_incident):
        """
        TDD Test: P2 severity for performance issues.
        Requirement: Slow performance = P2
        """
        assert EnrichmentService.determine_severity(p2_incident) == Severity.P2
    
    @pytest.mark.unit
    def test_determine_severity_p3_default(self, sample_incident):
        """
        TDD Test: P3 as default severity.
        Requirement: No P1/P2 keywords = P3 (default)
        """
        # Modify to ensure no P1/P2 keywords
        incident = IncidentCreate(
            title="Minor Issue",
            description="Need to update a report format",
            erp_module=ERPModule.HR,
            environment=Environment.TEST,
            business_unit="HR"
        )
        assert EnrichmentService.determine_severity(incident) == Severity.P3
    
    @pytest.mark.unit
    def test_determine_category_integration(self, integration_incident):
        """
        TDD Test: Integration failure category detection.
        Requirement: API/integration keywords = Integration Failure
        """
        assert EnrichmentService.determine_category(integration_incident) == Category.INTEGRATION_FAILURE
    
    @pytest.mark.unit
    def test_determine_category_security(self):
        """
        TDD Test: Security/access category detection.
        Requirement: Access/permission keywords = Security/Access
        """
        incident = IncidentCreate(
            title="Access Denied",
            description="User cannot login and access is denied",
            erp_module=ERPModule.HR,
            environment=Environment.PROD,
            business_unit="HR"
        )
        assert EnrichmentService.determine_category(incident) == Category.SECURITY_ACCESS
    
    @pytest.mark.unit
    def test_determine_category_data_issue(self):
        """
        TDD Test: Data issue category detection.
        Requirement: Data/duplicate keywords = Data Issue
        """
        incident = IncidentCreate(
            title="Duplicate Records",
            description="Found duplicate data in transactions",
            erp_module=ERPModule.GL,
            environment=Environment.PROD,
            business_unit="Finance"
        )
        assert EnrichmentService.determine_category(incident) == Category.DATA_ISSUE
    
    @pytest.mark.unit
    def test_determine_category_configuration(self):
        """
        TDD Test: Configuration issue category detection.
        Requirement: Config/setting keywords = Configuration Issue
        """
        incident = IncidentCreate(
            title="Wrong Configuration",
            description="System configuration settings are incorrect",
            erp_module=ERPModule.INVENTORY,
            environment=Environment.PROD,
            business_unit="Operations"
        )
        assert EnrichmentService.determine_category(incident) == Category.CONFIGURATION_ISSUE
    
    @pytest.mark.unit
    def test_determine_category_unknown(self):
        """
        TDD Test: Unknown category for unmatched incidents.
        Requirement: No category keywords = Unknown
        """
        incident = IncidentCreate(
            title="General Question",
            description="How do I generate a report?",
            erp_module=ERPModule.GL,
            environment=Environment.TEST,
            business_unit="Finance"
        )
        assert EnrichmentService.determine_category(incident) == Category.UNKNOWN
    
    @pytest.mark.unit
    def test_generate_summary(self, sample_incident):
        """
        TDD Test: Summary generation from title and description.
        Requirement: Summary = Title + first sentence
        """
        summary = EnrichmentService.generate_summary(sample_incident)
        assert sample_incident.title in summary
        assert len(summary) > 0
        assert isinstance(summary, str)
    
    @pytest.mark.unit
    def test_suggest_action_p1(self, p1_incident):
        """
        TDD Test: Action suggestion for P1 incidents.
        Requirement: P1 = Immediate escalation
        """
        category = Category.INTEGRATION_FAILURE
        severity = Severity.P1
        action = EnrichmentService.suggest_action(p1_incident, category, severity)
        assert "Immediate escalation" in action or "on-call" in action.lower()
        assert isinstance(action, str)
        assert len(action) > 0

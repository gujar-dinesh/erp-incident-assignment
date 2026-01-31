from typing import Dict
from app.models.incident import Severity, Category, IncidentCreate


class EnrichmentService:
    """
    Service responsible for enriching incident data with derived metadata.
    Uses rule-based heuristics to determine severity and category.
    """
    
    # Keywords that indicate high severity (P1)
    P1_KEYWORDS = [
        "critical", "down", "outage", "stuck", "blocked", "cannot process",
        "complete failure", "system down", "not working", "broken",
        "urgent", "emergency", "production down", "all users affected"
    ]
    
    # Keywords that indicate medium severity (P2)
    P2_KEYWORDS = [
        "slow", "delay", "performance", "lagging", "timeout", "intermittent",
        "some users", "degraded", "partial", "reduced functionality"
    ]
    
    # Category mapping: keywords -> category
    CATEGORY_KEYWORDS: Dict[Category, list] = {
        Category.INTEGRATION_FAILURE: [
            "integration", "api", "webhook", "connection", "sync", "import",
            "export", "interface", "endpoint", "service", "external system"
        ],
        Category.SECURITY_ACCESS: [
            "access", "permission", "authentication", "authorization", "login",
            "password", "credential", "security", "unauthorized", "forbidden",
            "user cannot", "locked out", "access denied"
        ],
        Category.DATA_ISSUE: [
            "data", "duplicate", "missing", "incorrect", "wrong", "corrupt",
            "invalid", "error in data", "data mismatch", "record", "transaction"
        ],
        Category.CONFIGURATION_ISSUE: [
            "configuration", "config", "setting", "setup", "parameter",
            "misconfigured", "wrong setting", "incorrect config"
        ]
    }
    
    @staticmethod
    def _normalize_text(text: str) -> str:
        """Convert text to lowercase for case-insensitive matching."""
        return text.lower()
    
    @staticmethod
    def determine_severity(incident: IncidentCreate) -> Severity:
        """
        Determine incident severity based on title and description content.
        
        Logic:
        - P1: Contains critical/urgent keywords indicating system-wide impact
        - P2: Contains keywords indicating performance or partial issues
        - P3: Default for all other cases
        """
        combined_text = f"{incident.title} {incident.description}"
        normalized = EnrichmentService._normalize_text(combined_text)
        
        # Check for P1 indicators
        for keyword in EnrichmentService.P1_KEYWORDS:
            if keyword in normalized:
                return Severity.P1
        
        # Check for P2 indicators
        for keyword in EnrichmentService.P2_KEYWORDS:
            if keyword in normalized:
                return Severity.P2
        
        # Default to P3
        return Severity.P3
    
    @staticmethod
    def determine_category(incident: IncidentCreate) -> Category:
        """
        Classify incident into a category based on content analysis.
        
        Uses keyword matching with priority order. If multiple categories match,
        returns the first one found in priority order.
        """
        combined_text = f"{incident.title} {incident.description}"
        normalized = EnrichmentService._normalize_text(combined_text)
        
        # Check categories in priority order
        for category, keywords in EnrichmentService.CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in normalized:
                    return category
        
        # Default to Unknown if no match
        return Category.UNKNOWN
    
    @staticmethod
    def generate_summary(incident: IncidentCreate) -> str:
        """
        Generate a short summary of the incident.
        Uses the title and first sentence of description.
        """
        title = incident.title
        description_first_sentence = incident.description.split('.')[0].strip()
        
        if len(description_first_sentence) > 100:
            description_first_sentence = description_first_sentence[:97] + "..."
        
        return f"{title}: {description_first_sentence}"
    
    @staticmethod
    def suggest_action(incident: IncidentCreate, category: Category, severity: Severity) -> str:
        """
        Suggest a next action based on category and severity.
        """
        if severity == Severity.P1:
            return "Immediate escalation required. Contact on-call engineer."
        
        if category == Category.INTEGRATION_FAILURE:
            return "Check integration logs and verify external system connectivity."
        
        if category == Category.SECURITY_ACCESS:
            return "Review user permissions and verify access configuration."
        
        if category == Category.DATA_ISSUE:
            return "Investigate data integrity and verify transaction logs."
        
        if category == Category.CONFIGURATION_ISSUE:
            return "Review system configuration settings and compare with baseline."
        
        return "Review incident details and assign to appropriate team."

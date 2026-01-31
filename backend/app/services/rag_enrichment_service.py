from typing import Dict, List, Tuple, Optional
from app.models.incident import IncidentCreate, Severity, Category, ERPModule, Environment
from app.services.enrichment_service import EnrichmentService
from app.services.embedding_service import EmbeddingService
from app.repositories.vector_repository import VectorRepositoryInterface
from app.config import settings
import json


class RAGEnrichmentService:
    """
    RAG-enhanced enrichment service with hybrid approach.
    
    Strategy:
    1. Try rule-based first (fast, free, works for 90% of cases)
    2. If low confidence or unknown category, use RAG with similar incidents
    3. Falls back gracefully if RAG unavailable
    
    This approach balances speed, cost, and accuracy.
    """
    
    def __init__(self, vector_repository: VectorRepositoryInterface):
        """
        Initialize RAG enrichment service.
        
        Args:
            vector_repository: Vector repository for similarity search
        """
        self.vector_repo = vector_repository
        self.embedding_service = EmbeddingService()
        self.rule_based_service = EnrichmentService()
        self.llm_client = None
        
        # Initialize LLM client if RAG is enabled
        if settings.use_rag and settings.openai_api_key:
            try:
                import openai
                self.llm_client = openai.OpenAI(api_key=settings.openai_api_key)
            except ImportError:
                print("Warning: OpenAI not available. RAG will use rule-based fallback.")
    
    def enrich_incident(self, incident: IncidentCreate) -> Dict:
        """
        Enrich incident with metadata using hybrid RAG approach.
        
        Args:
            incident: Incident to enrich
            
        Returns:
            Dictionary with: severity, category, summary, suggested_action,
            similar_incidents, enrichment_method
        """
        # Step 1: Try rule-based first (fast path for most cases)
        rule_result = self._enrich_rule_based(incident)
        
        # Step 2: Check if we should use RAG
        should_use_rag = self._should_use_rag(incident, rule_result)
        
        if not should_use_rag:
            return {
                **rule_result,
                'enrichment_method': 'rule_based',
                'similar_incidents': []
            }
        
        # Step 3: Use RAG enhancement
        try:
            rag_result = self._enrich_with_rag(incident, rule_result)
            return rag_result
        except Exception as e:
            # Fallback to rule-based if RAG fails
            print(f"RAG enrichment failed: {e}. Falling back to rule-based.")
            return {
                **rule_result,
                'enrichment_method': 'rule_based_fallback',
                'similar_incidents': []
            }
    
    def _should_use_rag(self, incident: IncidentCreate, rule_result: Dict) -> bool:
        """
        Determine if RAG should be used based on confidence.
        
        Uses RAG when:
        - RAG_FORCE_ALL is enabled (forces RAG for all incidents)
        - Category is Unknown (rule-based couldn't classify)
        - Description is very short (low confidence)
        - Similar incidents found (for learning from history)
        """
        # Force RAG for all incidents if configured
        if settings.rag_force_all:
            return True
        
        # Always use RAG if category is unknown
        if rule_result['category'] == Category.UNKNOWN:
            return True
        
        # Use RAG if description is very short (low confidence)
        if len(incident.description) < 50:
            return True
        
        # Check if we have similar incidents to learn from
        try:
            query_embedding = self.embedding_service.generate_incident_embedding(
                incident.title,
                incident.description
            )
            similar = self.vector_repo.find_similar(
                query_embedding,
                limit=1,
                filters={"status": "resolved"}
            )
            # Use RAG if we found similar incidents
            return len(similar) > 0
        except Exception:
            # If embedding generation fails, don't use RAG
            return False
    
    def _enrich_rule_based(self, incident: IncidentCreate) -> Dict:
        """Get rule-based enrichment result."""
        severity = self.rule_based_service.determine_severity(incident)
        category = self.rule_based_service.determine_category(incident)
        summary = self.rule_based_service.generate_summary(incident)
        suggested_action = self.rule_based_service.suggest_action(incident, category, severity)
        
        return {
            'severity': severity,
            'category': category,
            'summary': summary,
            'suggested_action': suggested_action
        }
    
    def _enrich_with_rag(
        self,
        incident: IncidentCreate,
        rule_result: Dict
    ) -> Dict:
        """
        Enrich using RAG with similar incidents.
        
        Args:
            incident: New incident
            rule_result: Rule-based result (for fallback)
            
        Returns:
            Enriched incident data
        """
        # Generate embedding for new incident
        query_embedding = self.embedding_service.generate_incident_embedding(
            incident.title,
            incident.description
        )
        
        # Find similar incidents
        similar_incidents = self.vector_repo.find_similar(
            query_embedding,
            limit=settings.rag_max_similar_incidents,
            filters={"status": "resolved"}
        )
        
        # If no similar incidents found, fall back to rule-based
        if not similar_incidents:
            return {
                **rule_result,
                'enrichment_method': 'rule_based',
                'similar_incidents': []
            }
        
        # Use LLM for classification if available
        if self.llm_client:
            try:
                classification = self._classify_with_llm(incident, similar_incidents)
                severity = classification['severity']
                category = classification['category']
            except Exception as e:
                print(f"LLM classification failed: {e}. Using rule-based.")
                severity = rule_result['severity']
                category = rule_result['category']
        else:
            # Use majority voting from similar incidents
            severity, category = self._classify_by_majority_vote(similar_incidents, rule_result)
        
        # Generate summary
        summary = self.rule_based_service.generate_summary(incident)
        
        # Generate action based on similar incidents
        suggested_action = self._generate_action_from_similar(
            severity,
            category,
            similar_incidents,
            rule_result['suggested_action']
        )
        
        return {
            'severity': severity,
            'category': category,
            'summary': summary,
            'suggested_action': suggested_action,
            'enrichment_method': 'rag',
            'similar_incidents': [
                {
                    'id': inc.id,
                    'title': inc.title,
                    'category': inc.category.value,
                    'severity': inc.severity.value,
                    'similarity_score': round(score, 3)
                }
                for inc, score in similar_incidents[:3]  # Top 3
            ]
        }
    
    def _classify_with_llm(
        self,
        incident: IncidentCreate,
        similar_incidents: List[Tuple]
    ) -> Dict:
        """Classify incident using LLM with context from similar incidents."""
        # Build context
        context = self._build_context(similar_incidents)
        
        # Create prompt
        prompt = self._create_classification_prompt(incident, context)
        
        # Call LLM
        response = self.llm_client.chat.completions.create(
            model="gpt-4o-mini",  # Cost-effective, still accurate
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert at classifying ERP incidents. "
                        "Analyze incidents and classify them accurately based on "
                        "similar past incidents. Return only valid JSON."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        # Parse response
        result = json.loads(response.choices[0].message.content)
        
        return {
            'severity': Severity(result['severity']),
            'category': Category(result['category'])
        }
    
    def _classify_by_majority_vote(
        self,
        similar_incidents: List[Tuple],
        rule_result: Dict
    ) -> Tuple[Severity, Category]:
        """
        Classify by majority vote from similar incidents.
        Used when LLM is not available.
        """
        if not similar_incidents:
            return rule_result['severity'], rule_result['category']
        
        # Count occurrences
        severity_counts = {}
        category_counts = {}
        
        for incident, score in similar_incidents:
            # Weight by similarity score
            weight = score
            
            severity_counts[incident.severity] = (
                severity_counts.get(incident.severity, 0) + weight
            )
            category_counts[incident.category] = (
                category_counts.get(incident.category, 0) + weight
            )
        
        # Get most common (weighted)
        severity = max(severity_counts.items(), key=lambda x: x[1])[0]
        category = max(category_counts.items(), key=lambda x: x[1])[0]
        
        return severity, category
    
    def _build_context(self, similar_incidents: List[Tuple]) -> str:
        """Build context string from similar incidents."""
        context_parts = []
        for incident, score in similar_incidents:
            context_parts.append(
                f"Similar Incident (similarity: {score:.2f}):\n"
                f"Title: {incident.title}\n"
                f"Description: {incident.description[:200]}...\n"
                f"Category: {incident.category.value}\n"
                f"Severity: {incident.severity.value}\n"
                f"Suggested Action: {incident.suggested_action}\n"
            )
        return "\n---\n".join(context_parts)
    
    def _create_classification_prompt(
        self,
        incident: IncidentCreate,
        context: str
    ) -> str:
        """Create prompt for LLM classification."""
        return f"""
Analyze this new ERP incident and classify it based on similar past incidents.

NEW INCIDENT:
Title: {incident.title}
Description: {incident.description}
ERP Module: {incident.erp_module.value}
Environment: {incident.environment.value}
Business Unit: {incident.business_unit}

SIMILAR PAST INCIDENTS (for reference):
{context}

Based on the new incident and similar past incidents, classify:
1. Severity: P1 (critical/urgent), P2 (medium), or P3 (low)
2. Category: Configuration Issue, Data Issue, Integration Failure, Security / Access, or Unknown

Return JSON format:
{{
    "severity": "P1|P2|P3",
    "category": "Configuration Issue|Data Issue|Integration Failure|Security / Access|Unknown",
    "reasoning": "Brief explanation of classification"
}}
"""
    
    def _generate_action_from_similar(
        self,
        severity: Severity,
        category: Category,
        similar_incidents: List[Tuple],
        fallback_action: str
    ) -> str:
        """Generate action suggestion based on similar incidents."""
        if not similar_incidents:
            return fallback_action
        
        # Get actions from similar incidents
        actions = [
            inc.suggested_action
            for inc, score in similar_incidents
            if inc.suggested_action
        ]
        
        if actions:
            # Use most common action or first one
            most_common = max(set(actions), key=actions.count)
            return f"{most_common} (Based on {len(similar_incidents)} similar resolved incidents)"
        
        return fallback_action

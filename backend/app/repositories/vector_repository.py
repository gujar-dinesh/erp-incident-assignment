from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Dict
from app.models.incident import IncidentResponse
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime, timedelta


class VectorRepositoryInterface(ABC):
    """
    Abstract interface for vector storage and similarity search.
    Allows easy swapping between in-memory, Pinecone, Weaviate, etc.
    """
    
    @abstractmethod
    def add_embedding(self, incident_id: str, embedding: List[float], metadata: Dict) -> None:
        """Store an embedding with associated metadata."""
        pass
    
    @abstractmethod
    def find_similar(
        self,
        query_embedding: List[float],
        limit: int = 5,
        filters: Optional[Dict] = None
    ) -> List[Tuple[IncidentResponse, float]]:
        """
        Find similar incidents using vector similarity.
        
        Args:
            query_embedding: Embedding vector to search for
            limit: Maximum number of results
            filters: Optional filters (e.g., {"status": "resolved"})
            
        Returns:
            List of (IncidentResponse, similarity_score) tuples
        """
        pass
    
    @abstractmethod
    def remove_embedding(self, incident_id: str) -> None:
        """Remove an embedding from storage."""
        pass
    
    @abstractmethod
    def get_embedding(self, incident_id: str) -> Optional[List[float]]:
        """Retrieve an embedding by incident ID."""
        pass


class InMemoryVectorRepository(VectorRepositoryInterface):
    """
    In-memory vector repository for MVP.
    Scales to ~10K-50K incidents efficiently.
    
    For production at scale, replace with Pinecone/Weaviate/Qdrant.
    """
    
    def __init__(self, incident_repository):
        """
        Initialize in-memory vector repository.
        
        Args:
            incident_repository: Repository to fetch full incident data
        """
        self.incident_repo = incident_repository
        # Storage: {incident_id: embedding}
        self._embeddings: Dict[str, List[float]] = {}
        # Metadata: {incident_id: {status, created_at, ...}}
        self._metadata: Dict[str, Dict] = {}
        # Cache for resolved incidents (refreshed periodically)
        self._resolved_incidents_cache: Optional[List[IncidentResponse]] = None
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl = timedelta(minutes=5)  # Refresh cache every 5 minutes
    
    def add_embedding(self, incident_id: str, embedding: List[float], metadata: Dict) -> None:
        """Store an embedding with metadata."""
        self._embeddings[incident_id] = embedding
        self._metadata[incident_id] = metadata
        # Invalidate cache when new incident is added
        self._resolved_incidents_cache = None
    
    def get_embedding(self, incident_id: str) -> Optional[List[float]]:
        """Retrieve an embedding by incident ID."""
        return self._embeddings.get(incident_id)
    
    def remove_embedding(self, incident_id: str) -> None:
        """Remove an embedding from storage."""
        self._embeddings.pop(incident_id, None)
        self._metadata.pop(incident_id, None)
        self._resolved_incidents_cache = None
    
    def _get_resolved_incidents(self) -> List[IncidentResponse]:
        """
        Get all resolved incidents (cached for performance).
        Only searches incidents that have embeddings.
        """
        # Check cache
        if (self._resolved_incidents_cache is not None and 
            self._cache_timestamp is not None and
            datetime.now() - self._cache_timestamp < self._cache_ttl):
            return self._resolved_incidents_cache
        
        # Fetch resolved incidents from repository
        resolved, _ = self.incident_repo.list_all(
            limit=10000,  # Reasonable limit for in-memory
            status="resolved"
        )
        
        # Filter to only those with embeddings
        incidents_with_embeddings = [
            inc for inc in resolved
            if inc.id in self._embeddings
        ]
        
        # Update cache
        self._resolved_incidents_cache = incidents_with_embeddings
        self._cache_timestamp = datetime.now()
        
        return incidents_with_embeddings
    
    def find_similar(
        self,
        query_embedding: List[float],
        limit: int = 5,
        filters: Optional[Dict] = None
    ) -> List[Tuple[IncidentResponse, float]]:
        """
        Find similar incidents using cosine similarity.
        
        Args:
            query_embedding: Query vector
            limit: Maximum results
            filters: Optional filters (e.g., {"status": "resolved"})
            
        Returns:
            List of (IncidentResponse, similarity_score) tuples
        """
        # Get candidates (default to resolved incidents)
        status_filter = filters.get("status", "resolved") if filters else "resolved"
        
        if status_filter == "resolved":
            candidates = self._get_resolved_incidents()
        else:
            # For other statuses, fetch from repository
            candidates, _ = self.incident_repo.list_all(
                limit=10000,
                status=status_filter
            )
            # Filter to those with embeddings
            candidates = [inc for inc in candidates if inc.id in self._embeddings]
        
        if not candidates:
            return []
        
        # Get embeddings for candidates
        candidate_embeddings = []
        candidate_incidents = []
        
        for incident in candidates:
            if incident.id in self._embeddings:
                candidate_embeddings.append(self._embeddings[incident.id])
                candidate_incidents.append(incident)
        
        if not candidate_embeddings:
            return []
        
        # Calculate cosine similarity
        query_vector = np.array(query_embedding).reshape(1, -1)
        candidate_vectors = np.array(candidate_embeddings)
        
        similarities = cosine_similarity(query_vector, candidate_vectors)[0]
        
        # Sort by similarity (highest first)
        similar_indices = np.argsort(similarities)[::-1]
        
        # Filter by minimum similarity threshold (0.7 = 70% similar)
        min_similarity = 0.7
        results = []
        
        for idx in similar_indices:
            if similarities[idx] >= min_similarity and len(results) < limit:
                results.append((candidate_incidents[idx], float(similarities[idx])))
        
        return results
    
    def get_stats(self) -> Dict:
        """Get statistics about stored embeddings."""
        return {
            "total_embeddings": len(self._embeddings),
            "cache_size": len(self._resolved_incidents_cache) if self._resolved_incidents_cache else 0,
            "cache_age_seconds": (
                (datetime.now() - self._cache_timestamp).total_seconds()
                if self._cache_timestamp else None
            )
        }

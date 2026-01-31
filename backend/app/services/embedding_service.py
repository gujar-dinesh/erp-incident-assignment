from typing import List, Optional
import openai
from app.config import settings


class EmbeddingService:
    """
    Service for generating vector embeddings for incident text.
    Uses OpenAI embeddings API (can be swapped for local models).
    """
    
    def __init__(self):
        self.model = "text-embedding-3-small"  # 1536 dimensions, cost-effective
        self.client = None
        
        if settings.use_rag and settings.openai_api_key:
            self.client = openai.OpenAI(api_key=settings.openai_api_key)
        elif settings.use_rag:
            raise ValueError(
                "USE_RAG is enabled but OPENAI_API_KEY is not set. "
                "Please set OPENAI_API_KEY in your .env file."
            )
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text string.
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        if not self.client:
            raise RuntimeError("OpenAI client not initialized. Check OPENAI_API_KEY.")
        
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            raise RuntimeError(f"Failed to generate embedding: {str(e)}")
    
    def generate_incident_embedding(self, title: str, description: str) -> List[float]:
        """
        Generate embedding for an incident (combines title and description).
        
        Args:
            title: Incident title
            description: Incident description
            
        Returns:
            List of floats representing the embedding vector
        """
        # Combine title and description for better semantic understanding
        combined_text = f"{title}\n\n{description}"
        return self.generate_embedding(combined_text)
    
    def generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in a single API call.
        More efficient than individual calls.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        if not self.client:
            raise RuntimeError("OpenAI client not initialized. Check OPENAI_API_KEY.")
        
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            raise RuntimeError(f"Failed to generate batch embeddings: {str(e)}")

import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Settings:
    aws_access_key_id: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY")
    aws_region: str = os.getenv("AWS_REGION", "us-east-1")
    dynamodb_table_name: str = os.getenv("DYNAMODB_TABLE_NAME", "erp_incidents")
    environment: str = os.getenv("ENVIRONMENT", "development")
    use_mock: bool = os.getenv("USE_MOCK", "false").lower() == "true"
    # RAG configuration
    use_rag: bool = os.getenv("USE_RAG", "false").lower() == "true"
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    rag_confidence_threshold: float = float(os.getenv("RAG_CONFIDENCE_THRESHOLD", "0.7"))
    rag_max_similar_incidents: int = int(os.getenv("RAG_MAX_SIMILAR_INCIDENTS", "5"))
    vector_db_type: str = os.getenv("VECTOR_DB_TYPE", "memory")  # memory, pinecone, weaviate
    rag_force_all: bool = os.getenv("RAG_FORCE_ALL", "false").lower() == "true"  # Force RAG for all incidents


settings = Settings()

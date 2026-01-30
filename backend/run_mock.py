"""
Backend server runner with mock storage (no AWS required).
Use this for development without DynamoDB setup.
"""
import uvicorn
import os

# Set mock mode
os.environ["USE_MOCK"] = "true"
os.environ["ENVIRONMENT"] = "development"
os.environ.pop("AWS_ACCESS_KEY_ID", None)
os.environ.pop("AWS_SECRET_ACCESS_KEY", None)

if __name__ == "__main__":
    print("=" * 60)
    print("Starting ERP Incident Portal API")
    print("Mode: MOCK STORAGE (in-memory)")
    print("=" * 60)
    print("\nStorage: In-memory mock (no AWS required)")
    print("Note: Data will be lost when server restarts")
    print("\nAPI Documentation:")
    print("  Swagger UI: http://localhost:8000/docs")
    print("  ReDoc:      http://localhost:8000/redoc")
    print("\nTo use real DynamoDB, run: python run.py")
    print("=" * 60)
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

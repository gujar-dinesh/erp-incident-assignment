"""
DEPRECATED: Use run_mock.py instead
This file is kept for backward compatibility.
"""
import sys
import os

# Redirect to run_mock.py
if __name__ == "__main__":
    print("⚠️  DEPRECATED: run_dev.py is deprecated.")
    print("   Please use: python run_mock.py")
    print("   Redirecting to run_mock.py...\n")
    
    # Import and run the mock runner
    from run_mock import *
    
    # Actually execute the run_mock logic
    os.environ["USE_MOCK"] = "true"
    os.environ["ENVIRONMENT"] = "development"
    os.environ.pop("AWS_ACCESS_KEY_ID", None)
    os.environ.pop("AWS_SECRET_ACCESS_KEY", None)
    
    import uvicorn
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

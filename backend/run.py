"""
Backend server runner with real DynamoDB storage.
Requires AWS credentials configured in .env file.
"""
import uvicorn
import os

# Ensure we're not in mock mode
os.environ.pop("USE_MOCK", None)

if __name__ == "__main__":
    print("=" * 60)
    print("Starting ERP Incident Portal API")
    print("Mode: REAL DynamoDB")
    print("=" * 60)
    
    # Check if AWS credentials are configured
    if not os.getenv("AWS_ACCESS_KEY_ID"):
        print("\n⚠️  WARNING: AWS credentials not found!")
        print("   The server will automatically use mock storage.")
        print("   To use real DynamoDB:")
        print("   1. Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in .env")
        print("   2. Create DynamoDB table (see README.md)")
        print("\n   For mock storage, run: python run_mock.py")
    else:
        print("\n✅ AWS credentials found")
        print("   Using DynamoDB table:", os.getenv("DYNAMODB_TABLE_NAME", "erp_incidents"))
    
    print("\nAPI Documentation:")
    print("  Swagger UI: http://localhost:8000/docs")
    print("  ReDoc:      http://localhost:8000/redoc")
    print("=" * 60)
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

"""
Script to create Global Secondary Indexes (GSI) for DynamoDB table.
Run this once to add GSI to your existing table.

Usage:
    python scripts/create_gsi.py
"""
import boto3
import os
from dotenv import load_dotenv

load_dotenv()

def create_gsi():
    """Create Global Secondary Indexes for efficient querying."""
    dynamodb = boto3.resource(
        'dynamodb',
        region_name=os.getenv('AWS_REGION', 'us-east-1'),
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )
    
    table_name = os.getenv('DYNAMODB_TABLE_NAME', 'erp_incidents')
    table = dynamodb.Table(table_name)
    
    print(f"Creating GSI for table: {table_name}")
    
    # GSI 1: Query by status and created_at (for listing incidents by status)
    try:
        table.update(
            AttributeDefinitions=[
                {'AttributeName': 'status', 'AttributeType': 'S'},
                {'AttributeName': 'created_at', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexUpdates=[
                {
                    'Create': {
                        'IndexName': 'status-created_at-index',
                        'KeySchema': [
                            {'AttributeName': 'status', 'KeyType': 'HASH'},
                            {'AttributeName': 'created_at', 'KeyType': 'RANGE'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'BillingMode': 'PAY_PER_REQUEST'
                    }
                }
            ]
        )
        print("✅ Created GSI: status-created_at-index")
    except Exception as e:
        if 'already exists' in str(e).lower():
            print("⚠️  GSI status-created_at-index already exists")
        else:
            print(f"❌ Error creating status-created_at-index: {e}")
    
    # GSI 2: Query by erp_module and severity (for filtering)
    try:
        table.update(
            AttributeDefinitions=[
                {'AttributeName': 'erp_module', 'AttributeType': 'S'},
                {'AttributeName': 'severity', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexUpdates=[
                {
                    'Create': {
                        'IndexName': 'module-severity-index',
                        'KeySchema': [
                            {'AttributeName': 'erp_module', 'KeyType': 'HASH'},
                            {'AttributeName': 'severity', 'KeyType': 'RANGE'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'BillingMode': 'PAY_PER_REQUEST'
                    }
                }
            ]
        )
        print("✅ Created GSI: module-severity-index")
    except Exception as e:
        if 'already exists' in str(e).lower():
            print("⚠️  GSI module-severity-index already exists")
        else:
            print(f"❌ Error creating module-severity-index: {e}")
    
    print("\n✅ GSI creation complete!")
    print("Note: GSI creation may take a few minutes. Check AWS Console for status.")

if __name__ == "__main__":
    create_gsi()

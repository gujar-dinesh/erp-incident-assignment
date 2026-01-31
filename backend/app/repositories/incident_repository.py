import boto3
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
from botocore.exceptions import ClientError
from botocore.config import Config
from boto3.dynamodb.conditions import Key, Attr
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.config import settings
from app.models.incident import IncidentResponse, IncidentStatus, Severity, Category


class IncidentRepository:
    """
    Repository pattern for DynamoDB operations.
    Abstracts data access logic from business logic.
    """
    
    def __init__(self):
        # Configure connection pooling and timeouts
        boto_config = Config(
            max_pool_connections=50,  # Connection pool size
            connect_timeout=5,         # 5 seconds to establish connection
            read_timeout=10,           # 10 seconds to read response
            retries={
                'max_attempts': 3,
                'mode': 'adaptive'    # Adaptive retry mode
            }
        )
        
        self.dynamodb = boto3.resource(
            'dynamodb',
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            config=boto_config
        )
        self.table = self.dynamodb.Table(settings.dynamodb_table_name)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(ClientError),
        reraise=True
    )
    def create(self, incident_data: dict) -> IncidentResponse:
        """
        Create a new incident in DynamoDB.
        Automatically retries on transient errors with exponential backoff.
        
        Args:
            incident_data: Dictionary containing incident fields
            
        Returns:
            IncidentResponse object
            
        Raises:
            Exception: If DynamoDB operation fails after retries
        """
        try:
            self.table.put_item(Item=incident_data)
            return self._dict_to_response(incident_data)
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code in ['ProvisionedThroughputExceededException', 'ThrottlingException']:
                # These will be retried automatically
                raise
            raise Exception(f"Failed to create incident: {str(e)}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(ClientError),
        reraise=True
    )
    def get_by_id(self, incident_id: str) -> Optional[IncidentResponse]:
        """
        Retrieve an incident by ID.
        Automatically retries on transient errors with exponential backoff.
        
        Args:
            incident_id: Unique identifier of the incident
            
        Returns:
            IncidentResponse if found, None otherwise
        """
        try:
            response = self.table.get_item(Key={'id': incident_id})
            if 'Item' in response:
                return self._dict_to_response(response['Item'])
            return None
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code in ['ProvisionedThroughputExceededException', 'ThrottlingException']:
                raise
            raise Exception(f"Failed to retrieve incident: {str(e)}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(ClientError),
        reraise=True
    )
    def list_all(
        self, 
        limit: int = 50,
        last_key: Optional[Dict[str, Any]] = None,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        erp_module: Optional[str] = None
    ) -> Tuple[List[IncidentResponse], Optional[Dict[str, Any]]]:
        """
        List incidents with pagination and filtering support.
        Uses GSI for efficient querying instead of scan.
        
        Args:
            limit: Maximum number of incidents to return (default: 50)
            last_key: Pagination token from previous request
            status: Filter by status (uses GSI if provided)
            severity: Filter by severity
            erp_module: Filter by ERP module
            
        Returns:
            Tuple of (list of incidents, next_page_token)
        """
        try:
            # If status filter provided, use GSI for efficient querying
            if status:
                return self._query_by_status(status, limit, last_key, severity, erp_module)
            
            # If module + severity filter, use module-severity-index
            if erp_module and severity:
                return self._query_by_module_severity(erp_module, severity, limit, last_key)
            
            # Fallback to scan only if no filters (less efficient but works)
            # In production, should always use status filter or other GSI
            return self._scan_with_filters(limit, last_key, severity, erp_module)
            
        except ClientError as e:
            raise Exception(f"Failed to list incidents: {str(e)}")
    
    def _query_by_status(
        self,
        status: str,
        limit: int,
        last_key: Optional[Dict[str, Any]],
        severity: Optional[str] = None,
        erp_module: Optional[str] = None
    ) -> Tuple[List[IncidentResponse], Optional[Dict[str, Any]]]:
        """Query incidents by status using status-created_at-index GSI."""
        key_condition = Key('status').eq(status)
        
        # Build filter expression for additional filters
        filter_expression = None
        if severity:
            filter_expression = Attr('severity').eq(severity)
        if erp_module:
            if filter_expression:
                filter_expression = filter_expression & Attr('erp_module').eq(erp_module)
            else:
                filter_expression = Attr('erp_module').eq(erp_module)
        
        query_params = {
            'IndexName': 'status-created_at-index',
            'KeyConditionExpression': key_condition,
            'Limit': limit,
            'ScanIndexForward': False  # Descending order (newest first)
        }
        
        if filter_expression:
            query_params['FilterExpression'] = filter_expression
        
        if last_key:
            query_params['ExclusiveStartKey'] = last_key
        
        response = self.table.query(**query_params)
        
        incidents = [self._dict_to_response(item) for item in response.get('Items', [])]
        next_key = response.get('LastEvaluatedKey')
        
        return incidents, next_key
    
    def _query_by_module_severity(
        self,
        erp_module: str,
        severity: str,
        limit: int,
        last_key: Optional[Dict[str, Any]]
    ) -> Tuple[List[IncidentResponse], Optional[Dict[str, Any]]]:
        """Query incidents by module and severity using module-severity-index GSI."""
        key_condition = Key('erp_module').eq(erp_module) & Key('severity').eq(severity)
        
        query_params = {
            'IndexName': 'module-severity-index',
            'KeyConditionExpression': key_condition,
            'Limit': limit,
            'ScanIndexForward': False
        }
        
        if last_key:
            query_params['ExclusiveStartKey'] = last_key
        
        response = self.table.query(**query_params)
        
        incidents = [self._dict_to_response(item) for item in response.get('Items', [])]
        # Sort by created_at in memory (could add created_at to GSI if needed)
        incidents.sort(key=lambda x: x.created_at, reverse=True)
        next_key = response.get('LastEvaluatedKey')
        
        return incidents, next_key
    
    def _scan_with_filters(
        self,
        limit: int,
        last_key: Optional[Dict[str, Any]],
        severity: Optional[str] = None,
        erp_module: Optional[str] = None
    ) -> Tuple[List[IncidentResponse], Optional[Dict[str, Any]]]:
        """
        Fallback scan method with filters.
        Less efficient than query - should be avoided in production.
        """
        filter_expression = None
        
        if severity:
            filter_expression = Attr('severity').eq(severity)
        if erp_module:
            if filter_expression:
                filter_expression = filter_expression & Attr('erp_module').eq(erp_module)
            else:
                filter_expression = Attr('erp_module').eq(erp_module)
        
        scan_params = {
            'Limit': limit
        }
        
        if filter_expression:
            scan_params['FilterExpression'] = filter_expression
        
        if last_key:
            scan_params['ExclusiveStartKey'] = last_key
        
        response = self.table.scan(**scan_params)
        
        incidents = [self._dict_to_response(item) for item in response.get('Items', [])]
        # Sort by created_at descending
        incidents.sort(key=lambda x: x.created_at, reverse=True)
        next_key = response.get('LastEvaluatedKey')
        
        return incidents, next_key
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(ClientError),
        reraise=True
    )
    def update(self, incident_id: str, update_data: dict) -> Optional[IncidentResponse]:
        """
        Update an existing incident.
        Automatically retries on transient errors with exponential backoff.
        
        Args:
            incident_id: Unique identifier of the incident
            update_data: Dictionary of fields to update
            
        Returns:
            Updated IncidentResponse if found, None otherwise
        """
        try:
            # Build update expression
            update_expression_parts = []
            expression_attribute_values = {}
            expression_attribute_names = {}
            
            for key, value in update_data.items():
                if key == 'id':
                    continue
                update_expression_parts.append(f"#{key} = :{key}")
                expression_attribute_names[f"#{key}"] = key
                expression_attribute_values[f":{key}"] = value
            
            if not update_expression_parts:
                return self.get_by_id(incident_id)
            
            # Always update updated_at timestamp
            update_expression_parts.append("#updated_at = :updated_at")
            expression_attribute_names["#updated_at"] = "updated_at"
            expression_attribute_values[":updated_at"] = datetime.utcnow().isoformat()
            
            update_expression = "SET " + ", ".join(update_expression_parts)
            
            response = self.table.update_item(
                Key={'id': incident_id},
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_attribute_names,
                ExpressionAttributeValues=expression_attribute_values,
                ReturnValues='ALL_NEW'
            )
            
            return self._dict_to_response(response['Attributes'])
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'ResourceNotFoundException':
                return None
            if error_code in ['ProvisionedThroughputExceededException', 'ThrottlingException']:
                raise
            raise Exception(f"Failed to update incident: {str(e)}")
    
    def _dict_to_response(self, item: dict) -> IncidentResponse:
        """Convert DynamoDB item dictionary to IncidentResponse model."""
        return IncidentResponse(
            id=item['id'],
            title=item['title'],
            description=item['description'],
            erp_module=item['erp_module'],
            environment=item['environment'],
            business_unit=item['business_unit'],
            severity=Severity(item['severity']),
            category=Category(item['category']),
            status=IncidentStatus(item['status']),
            created_at=datetime.fromisoformat(item['created_at']),
            updated_at=datetime.fromisoformat(item['updated_at']),
            summary=item.get('summary'),
            suggested_action=item.get('suggested_action')
        )

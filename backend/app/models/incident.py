from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class IncidentStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class Severity(str, Enum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class Category(str, Enum):
    CONFIGURATION_ISSUE = "Configuration Issue"
    DATA_ISSUE = "Data Issue"
    INTEGRATION_FAILURE = "Integration Failure"
    SECURITY_ACCESS = "Security / Access"
    UNKNOWN = "Unknown"


class ERPModule(str, Enum):
    AP = "AP"
    AR = "AR"
    GL = "GL"
    INVENTORY = "Inventory"
    HR = "HR"
    PAYROLL = "Payroll"


class Environment(str, Enum):
    PROD = "Prod"
    TEST = "Test"


class IncidentCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    erp_module: ERPModule
    environment: Environment
    business_unit: str = Field(..., min_length=1, max_length=100)


class IncidentUpdate(BaseModel):
    status: Optional[IncidentStatus] = None
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1)


class IncidentResponse(BaseModel):
    id: str
    title: str
    description: str
    erp_module: str
    environment: str
    business_unit: str
    severity: Severity
    category: Category
    status: IncidentStatus
    created_at: datetime
    updated_at: datetime
    summary: Optional[str] = None
    suggested_action: Optional[str] = None

    class Config:
        from_attributes = True

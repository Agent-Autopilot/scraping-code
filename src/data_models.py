"""Data models for the property management system."""

from typing import Dict, List, Optional
from dataclasses import dataclass
from dataclasses_json import dataclass_json

@dataclass_json
@dataclass
class Address:
    """Physical address with street, city, state, and zip code."""
    street: str
    city: str
    state: str
    zip: str

@dataclass_json
@dataclass
class ContactInfo:
    """Contact information including email, phone, and address."""
    email: Optional[str] = None  # Changed to Optional since not all contacts need email
    phone: Optional[str] = None
    address: Optional[Address] = None

@dataclass_json
@dataclass
class Document:
    """Document metadata including type, URL, and upload information."""
    id: str
    type: str  # e.g., 'lease', 'insurance', etc.
    url: str
    name: Optional[str] = None
    uploadDate: Optional[str] = None  # ISO format date string

@dataclass_json
@dataclass
class Photo:
    """Photo metadata including URL and descriptive information."""
    id: str
    url: str
    dateTaken: Optional[str] = None  # ISO format date string
    description: Optional[str] = None

@dataclass_json
@dataclass
class Lease:
    """Lease agreement details including dates, amounts, and relationships."""
    propertyId: str
    unitId: str
    tenantId: str
    startDate: str  # ISO format date string
    endDate: str    # ISO format date string
    rentAmount: float
    securityDeposit: Optional[float] = None
    dueDate: Optional[int] = None  # Day of month (1-31)
    documents: Optional[List[Document]] = None

@dataclass_json
@dataclass
class Tenant:
    """Tenant information including personal details and lease."""
    name: str
    contactInfo: ContactInfo
    ssn: Optional[str] = None  # Format: XXX-XX-XXXX
    lease: Optional[Lease] = None
    documents: Optional[List[Document]] = None

@dataclass_json
@dataclass
class Unit:
    """Property unit information including current tenant and documentation."""
    unitNumber: str
    propertyId: str
    currentTenant: Optional[Tenant] = None
    photos: Optional[List[Photo]] = None
    documents: Optional[List[Document]] = None

@dataclass_json
@dataclass
class Entity:
    """Legal entity (person or organization) with contact and tax information."""
    name: str
    type: str  # e.g., 'LLC', 'individual', etc.
    contactInfo: ContactInfo
    taxId: Optional[str] = None  # EIN or SSN
    documents: Optional[List[Document]] = None

@dataclass_json
@dataclass
class Property:
    """Property information including location, ownership, and units."""
    name: str
    address: Address
    owner: Entity
    units: Optional[List[Unit]] = None
    documents: Optional[List[Document]] = None 
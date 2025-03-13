"""Data models for the property management system."""

from typing import Dict, List, Optional
from dataclasses import dataclass
from dataclasses_json import dataclass_json

@dataclass_json
@dataclass
class Address:
    """Physical address with street, city, state, and zip code."""
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None

@dataclass_json
@dataclass
class ContactInfo:
    """Contact information including email, phone, and address."""
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[Address] = None

@dataclass_json
@dataclass
class Document:
    """Document metadata including type, URL, and upload information."""
    id: str  # Only ID is required
    type: Optional[str] = None  # e.g., 'lease', 'insurance', etc.
    url: Optional[str] = None
    name: Optional[str] = None
    uploadDate: Optional[str] = None  # ISO format date string

@dataclass_json
@dataclass
class Photo:
    """Photo metadata including URL and descriptive information."""
    id: str  # Only ID is required
    url: Optional[str] = None
    dateTaken: Optional[str] = None  # ISO format date string
    description: Optional[str] = None

@dataclass_json
@dataclass
class Lease:
    """Lease agreement details including dates, amounts, and relationships."""
    # Only IDs are required to establish relationships
    propertyId: str
    unitId: str
    tenantId: str
    # All other fields are optional
    startDate: Optional[str] = None  # ISO format date string
    endDate: Optional[str] = None    # ISO format date string
    rentAmount: Optional[float] = None
    securityDeposit: Optional[float] = None
    dueDate: Optional[int] = None  # Day of month (1-31)
    documents: Optional[List[Document]] = None

@dataclass_json
@dataclass
class Tenant:
    """Tenant information including personal details and lease."""
    name: str  # Only name is required as ID
    contactInfo: Optional[ContactInfo] = None
    ssn: Optional[str] = None  # Format: XXX-XX-XXXX
    lease: Optional[Lease] = None
    documents: Optional[List[Document]] = None

@dataclass_json
@dataclass
class Unit:
    """Property unit information including current tenant and documentation."""
    unitNumber: str  # Only unit number is required as ID
    propertyId: str  # Property relationship is required
    currentTenant: Optional[Tenant] = None
    photos: Optional[List[Photo]] = None
    documents: Optional[List[Document]] = None

@dataclass_json
@dataclass
class Entity:
    """Legal entity (person or organization) with contact and tax information."""
    name: str  # Only name is required as ID
    type: Optional[str] = None  # e.g., 'LLC', 'individual', etc.
    contactInfo: Optional[ContactInfo] = None
    taxId: Optional[str] = None  # EIN or SSN
    documents: Optional[List[Document]] = None

@dataclass_json
@dataclass
class Property:
    """Property information including location, ownership, and units."""
    name: str  # Only name is required as ID
    address: Optional[Address] = None
    owner: Optional[Entity] = None
    units: Optional[List[Unit]] = None
    documents: Optional[List[Document]] = None 
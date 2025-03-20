"""Data models for the property management system.

This module defines the core data structures used throughout the property management system.
Each class represents a key entity in the property management domain and is implemented
as a dataclass with JSON serialization support.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from dataclasses_json import dataclass_json

@dataclass_json
@dataclass
class Address:
    """Physical address with street, city, state, and zip code.
    
    Represents a complete physical location including street address, city, state, and postal code.
    """
    street: Optional[str] = None  # Street address including unit/apt number
    city: Optional[str] = None    # City name
    state: Optional[str] = None   # State/province (2-letter code for US)
    zip: Optional[str] = None     # Postal/ZIP code

@dataclass_json
@dataclass
class ContactInfo:
    """Contact information including email, phone, and address.
    
    Stores all contact details for an entity, tenant, or other party.
    """
    email: Optional[str] = None    # Primary email address
    phone: Optional[str] = None    # Phone number
    address: Optional[Address] = None  # Optional mailing/physical address

@dataclass_json
@dataclass
class Document:
    """Document metadata including type, URL, and upload information.
    
    Represents any document associated with properties, units, tenants, or leases.
    """
    id: str  # Only ID is required - Unique identifier for the document
    type: Optional[str] = None  # e.g., 'lease', 'insurance', etc.
    url: Optional[str] = None   # URL to access the document
    name: Optional[str] = None  # Optional document name
    uploadDate: Optional[str] = None  # ISO format date string for upload date

@dataclass_json
@dataclass
class Photo:
    """Photo metadata including URL and descriptive information.
    
    Represents photos associated with properties or units.
    """
    id: str  # Only ID is required - Unique identifier for the photo
    url: Optional[str] = None  # URL to access the photo
    dateTaken: Optional[str] = None  # ISO format date string when photo was taken
    description: Optional[str] = None  # Optional photo description

@dataclass_json
@dataclass
class Lease:
    """Lease agreement details including dates, amounts, and relationships.
    
    Represents a rental agreement between a tenant and property owner for a specific unit.
    """
    # Only IDs are required to establish relationships
    propertyId: str  # Reference to the rented property
    unitId: str      # Reference to the rented unit
    tenantId: str    # Reference to the tenant
    # All other fields are optional
    startDate: Optional[str] = None  # ISO format date string for lease start date
    endDate: Optional[str] = None    # ISO format date string for lease end date
    rentAmount: Optional[float] = None  # Monthly rent amount
    securityDeposit: Optional[float] = None  # Security deposit amount
    dueDate: Optional[str] = None  # Day of month rent is due (1-31) or text description
    documents: Optional[List[Document]] = None  # Optional lease documents

@dataclass_json
@dataclass
class Tenant:
    """Tenant information including personal details and lease.
    
    Represents a person renting a unit with their contact information and lease details.
    """
    name: str  # Only name is required as ID - Legal name of the tenant
    contactInfo: Optional[ContactInfo] = None  # Contact information for the tenant
    ssn: Optional[str] = None  # Social security number for background check/identification
    lease: Optional[Lease] = None  # Current lease agreement
    documents: Optional[List[Document]] = None  # Optional tenant documents

@dataclass_json
@dataclass
class Unit:
    """Property unit information including current tenant and documentation.
    
    Represents an individual unit within a property that can be rented.
    """
    unitNumber: str  # Only unit number is required as ID - Unit identifier within the property
    propertyId: str  # Property relationship is required - Reference to parent property
    currentTenant: Optional[Tenant] = None  # Current tenant, if unit is occupied
    photos: Optional[List[Photo]] = None  # Array of photo URLs for the unit
    documents: Optional[List[Document]] = None  # Optional unit documents

@dataclass_json
@dataclass
class Entity:
    """Legal entity (person or organization) with contact and tax information.
    
    Represents an owner (individual or business) of one or more properties.
    """
    name: str  # Only name is required as ID - Legal name of individual or business
    type: Optional[str] = None  # e.g., 'INDIVIDUAL', 'LLC', etc. - Type of ownership entity
    contactInfo: Optional[ContactInfo] = None  # Contact information for the entity
    taxId: Optional[str] = None  # EIN or SSN - Tax ID (SSN for individuals, EIN for businesses)
    documents: Optional[List[Document]] = None  # Optional entity documents

@dataclass_json
@dataclass
class Property:
    """Property information including location, ownership, and units.
    
    Represents a real estate property with its address, owner, and associated units.
    """
    name: str  # Only name is required as ID - Unique identifier for the property
    address: Optional[Address] = None  # Physical location of the property
    owner: Optional[Entity] = None  # Owner (individual or business) of the property
    units: Optional[List[Unit]] = None  # List of all units within this property
    documents: Optional[List[Document]] = None  # Optional property documents 
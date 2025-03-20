"""Data models for the property management system.

This module defines the core data structures used throughout the property management system.
Each class represents a key entity in the property management domain and is implemented
as a dataclass with JSON serialization support.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
import uuid

def generate_id() -> str:
    """Generate a unique ID string for model instances."""
    return str(uuid.uuid4())

@dataclass_json
@dataclass
class Address:
    """Physical address with street, city, state, and zip code.
    
    Represents a complete physical location including street address, city, state, and postal code.
    """
    id: str = field(default_factory=generate_id)  # Unique identifier
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
    id: str = field(default_factory=generate_id)  # Unique identifier
    email: Optional[str] = None    # Primary email address
    phone: Optional[str] = None    # Phone number
    addressId: Optional[str] = None  # Reference to the address ID
    address: Optional[Address] = None  # Optional mailing/physical address

@dataclass_json
@dataclass
class Lease:
    """Lease agreement details including dates, amounts, and relationships.
    
    Represents a rental agreement between a tenant and property owner for a specific unit.
    """
    id: str = field(default_factory=generate_id)  # Unique identifier
    propertyId: Optional[str] = None  # Reference to the property ID
    unitId: Optional[str] = None      # Reference to the unit ID
    tenantId: Optional[str] = None    # Reference to the tenant ID
    startDate: Optional[str] = None  # ISO format date string for lease start date
    endDate: Optional[str] = None    # ISO format date string for lease end date
    rentAmount: Optional[float] = None  # Monthly rent amount
    securityDeposit: Optional[float] = None  # Security deposit amount
    dueDate: Optional[str] = None  # Day of month rent is due (1-31) or text description

@dataclass_json
@dataclass
class Tenant:
    """Tenant information including personal details and lease.
    
    Represents a person renting a unit with their contact information and lease details.
    """
    id: str = field(default_factory=generate_id)  # Unique identifier
    name: Optional[str] = None  # Legal name of the tenant
    contactInfoId: Optional[str] = None  # Reference to the contact info ID
    contactInfo: Optional[ContactInfo] = None  # Contact information for the tenant
    ssn: Optional[str] = None  # Social security number for background check/identification
    leaseId: Optional[str] = None  # Reference to the lease ID
    lease: Optional[Lease] = None  # Current lease agreement

@dataclass_json
@dataclass
class Unit:
    """Property unit information including current tenant and documentation.
    
    Represents an individual unit within a property that can be rented.
    """
    id: str = field(default_factory=generate_id)  # Unique identifier
    unitNumber: Optional[str] = None  # Unit identifier within the property
    propertyId: Optional[str] = None  # Reference to parent property ID
    currentTenantId: Optional[str] = None  # Reference to the current tenant ID
    currentTenant: Optional[Tenant] = None  # Current tenant, if unit is occupied

@dataclass_json
@dataclass
class Entity:
    """Legal entity (person or organization) with contact and tax information.
    
    Represents an owner (individual or business) of one or more properties.
    """
    id: str = field(default_factory=generate_id)  # Unique identifier
    name: Optional[str] = None  # Legal name of individual or business
    type: Optional[str] = None  # e.g., 'INDIVIDUAL', 'LLC', etc. - Type of ownership entity
    contactInfoId: Optional[str] = None  # Reference to the contact info ID
    contactInfo: Optional[ContactInfo] = None  # Contact information for the entity
    taxId: Optional[str] = None  # EIN or SSN - Tax ID (SSN for individuals, EIN for businesses)

@dataclass_json
@dataclass
class Property:
    """Property information including location, ownership, and units.
    
    Represents a real estate property with its address, owner, and associated units.
    """
    id: str = field(default_factory=generate_id)  # Unique identifier
    name: Optional[str] = None  # Name or description of the property
    addressId: Optional[str] = None  # Reference to the address ID
    address: Optional[Address] = None  # Physical location of the property
    ownerId: Optional[str] = None  # Reference to the owner ID
    owner: Optional[Entity] = None  # Owner (individual or business) of the property
    unitIds: Optional[List[str]] = None  # List of unit IDs
    units: Optional[List[Unit]] = None  # List of all units within this property

from typing import Dict, List, Optional
from dataclasses import dataclass
from dataclasses_json import dataclass_json

@dataclass_json
@dataclass
class Address:
    street: str
    city: str
    state: str
    zip: str

@dataclass_json
@dataclass
class ContactInfo:
    email: str
    phone: Optional[str] = None
    address: Optional[Address] = None

@dataclass_json
@dataclass
class Document:
    id: str
    type: str
    url: str
    name: Optional[str] = None
    uploadDate: Optional[str] = None

@dataclass_json
@dataclass
class Photo:
    id: str
    url: str
    dateTaken: Optional[str] = None
    description: Optional[str] = None

@dataclass_json
@dataclass
class Lease:
    propertyId: str
    unitId: str
    tenantId: str
    startDate: str
    endDate: str
    rentAmount: float
    securityDeposit: Optional[float] = None
    dueDate: Optional[int] = None
    documents: Optional[List[Document]] = None

@dataclass_json
@dataclass
class Tenant:
    name: str
    contactInfo: ContactInfo
    ssn: Optional[str] = None
    lease: Optional[Lease] = None
    documents: Optional[List[Document]] = None

@dataclass_json
@dataclass
class Unit:
    unitNumber: str
    propertyId: str
    currentTenant: Optional[Tenant] = None
    photos: Optional[List[Photo]] = None
    documents: Optional[List[Document]] = None

@dataclass_json
@dataclass
class Entity:
    name: str
    type: str
    contactInfo: ContactInfo
    taxId: Optional[str] = None
    documents: Optional[List[Document]] = None

@dataclass_json
@dataclass
class Property:
    name: str
    address: Address
    owner: Entity
    units: Optional[List[Unit]] = None
    documents: Optional[List[Document]] = None 
# Core Data Structures

## Property
```typescript
interface Property {
  name: string;                   // Unique identifier for the property
  address: Address;               // Physical location of the property
  owner: Entity;                  // Owner (individual or business) of the property
  units?: Unit[];                 // List of all units within this property
  expenses?: Expense[];           // Optional list of property expenses
  documents?: Document[];         // Optional property documents
}
```

## Entity (Owner/Business)
```typescript
interface Entity {
  name: string;                   // Legal name of individual or business
  type: 'INDIVIDUAL' | 'LLC';     // Type of ownership entity
  contactInfo: ContactInfo;       // Contact information for the entity
  taxId?: string;                 // SSN for individuals, EIN for businesses
  properties?: Property[];        // List of properties owned by this entity
  documents?: Document[];         // Optional entity documents
}
```

## Unit
```typescript
interface Unit {
  unitNumber: string;            // Unit identifier within the property (e.g., "Apt 2B")
  propertyId: string;            // Reference to parent property
  currentTenant?: Tenant;        // Current tenant, if unit is occupied
  photos?: Photo[];             // Array of photo URLs for the unit
  documents?: Document[];        // Optional unit documents
}
```

## Tenant
```typescript
interface Tenant {
  name: string;                  // Legal name of the tenant
  contactInfo: ContactInfo;      // Contact information for the tenant
  ssn?: string;                 // Social security number for background check/identification
  lease?: Lease;                // Current lease agreement
  documents?: Document[];       // Optional tenant documents
}
```

## Lease
```typescript
interface Lease {
  propertyId: string;           // Reference to the rented property
  unitId: string;               // Reference to the rented unit
  tenantId: string;             // Reference to the tenant
  startDate: Date;              // Lease start date
  endDate: Date;                // Lease end date
  rentAmount: number;           // Monthly rent amount
  securityDeposit?: number;     // Optional security deposit amount
  dueDate?: number;             // Day of month rent is due (1-31)
  documents?: Document[];       // Optional lease documents
}
```

## Supporting Types
```typescript
interface ContactInfo {
  email: string;                // Primary email address
  phone?: string;               // Optional phone number
  address?: Address;            // Optional mailing/physical address
}

interface Address {
  street: string;               // Street address including unit/apt number
  city: string;                 // City name
  state: string;                // State/province (2-letter code for US)
  zip: string;                  // Postal/ZIP code
}

interface Document {
  id: string;                   // Unique identifier for the document
  type: string;                 // Document type
  url: string;                  // URL to access the document
  name?: string;                // Optional document name
  uploadDate?: Date;            // Optional upload date
}

interface Photo {
  id: string;                   // Unique identifier for the photo
  url: string;                  // URL to access the photo
  dateTaken?: Date;            // Optional date when photo was taken
  description?: string;         // Optional photo description
}
```
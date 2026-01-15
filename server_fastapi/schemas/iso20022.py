from datetime import date
from enum import Enum

from pydantic import BaseModel, Field, field_validator

# IVMS101 Standard (2026 Revision)
# InterVASP Messaging Standard for Article 16 (Travel Rule)


class AddressType(str, Enum):
    RESIDENTIAL = "HOME"
    BUSINESS = "BIZZ"
    GEOGRAPHIC = "GEOG"


class NationalIdentifierType(str, Enum):
    PASSPORT = "PASS"
    NATIONAL_ID = "NIDN"
    TAX_ID = "TXID"


class Address(BaseModel):
    """
    Structured address format complying with ISO 20022 PostalAddress.
    """

    address_type: AddressType = Field(..., description="Nature of the address")
    department: str | None = Field(None, max_length=70)
    sub_department: str | None = Field(None, max_length=70)
    street_name: str | None = Field(None, max_length=70)
    building_number: str | None = Field(None, max_length=16)
    building_name: str | None = Field(None, max_length=35)
    post_code: str | None = Field(None, max_length=16)
    town_name: str = Field(..., max_length=35)
    country_sub_division: str | None = Field(None, max_length=35)
    country: str = Field(
        ...,
        min_length=2,
        max_length=2,
        pattern="^[A-Z]{2}$",
        description="ISO 3166-1 alpha-2 code",
    )

    @field_validator("country")
    def validate_country(cls, v):
        # In a real app, validate against a full ISO country list
        return v.upper()


class NationalIdentifier(BaseModel):
    id_type: NationalIdentifierType
    id_value: str = Field(..., max_length=35)
    issuing_country: str = Field(..., min_length=2, max_length=2, pattern="^[A-Z]{2}$")


class NaturalPerson(BaseModel):
    """
    IVMS101 Natural Person
    """

    primary_identifier: str = Field(
        ..., max_length=50, description="Legal Name (Last Name, First Name)"
    )
    secondary_identifier: str | None = Field(None, max_length=50)
    date_of_birth: date | None = None
    place_of_birth: str | None = Field(None, max_length=35)
    national_id: NationalIdentifier | None = None
    address: Address | None = None


class LegalPerson(BaseModel):
    """
    IVMS101 Legal Person (Corporate)
    """

    legal_name: str = Field(..., max_length=100)
    registration_authority: str | None = Field(None, max_length=35)
    registration_number: str | None = Field(None, max_length=35)
    address: Address | None = None


class Originator(BaseModel):
    account_number: str = Field(
        ..., max_length=34, description="IBAN or internal wallet ID"
    )
    natural_person: NaturalPerson | None = None
    legal_person: LegalPerson | None = None

    @field_validator("account_number")
    def validate_account(cls, v):
        if not v.isalnum():
            raise ValueError("Account number must be alphanumeric")
        return v


class Beneficiary(BaseModel):
    account_number: str = Field(..., max_length=34)
    natural_person: NaturalPerson | None = None
    legal_person: LegalPerson | None = None


class TravelRulePayload(BaseModel):
    """
    Full payload for an inter-VASP transfer requirng IVMS101 data.
    """

    originator: Originator
    beneficiary: Beneficiary
    asset: str = Field(..., min_length=3, max_length=10)
    amount: str = Field(..., pattern=r"^\d+(\.\d+)?$")  # String for Decimal precision

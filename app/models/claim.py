"""
Dataverse Claim Models
Defines the structure of claims and service lines from Dataverse.
"""
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from .service_line import ServiceLine  # Import the comprehensive model


class Claim(BaseModel):
    """Claim entity from Dataverse with correct field names"""
    
    # Core identifiers
    smvs_claimid: str
    smvs_name: Optional[str] = None
    
    # Financial fields
    smvs_claimed_amount: Optional[float] = Field(None, description="Total claimed amount")
    smvs_expected_amount_claim: Optional[float] = None
    smvs_balance_currency: Optional[float] = None
    smvs_recieved_amount: Optional[float] = None
    
    # Status fields
    smvs_claimstatus: Optional[int] = Field(None, description="Claim status code")
    smvs_internal_state: Optional[int] = None
    statuscode: Optional[int] = None
    statecode: Optional[int] = None
    
    # Error and remarks
    smvs_remark: Optional[str] = Field(None, description="Claim remarks or failure reason")
    smvs_error_description: Optional[str] = None
    
    # Dates
    smvs_fulfilleddate: Optional[str] = None
    createdon: Optional[str] = None
    modifiedon: Optional[str] = None
    
    # Patient and provider references
    _smvs_patientid_value: Optional[str] = None
    _smvs_rendering_provider_key_value: Optional[str] = None
    _smvs_ordering_physician_key_value: Optional[str] = None
    _smvs_insuranceorganization_value: Optional[str] = None
    
    # Claim details
    smvs_claim_type: Optional[int] = None
    smvs_internal_claim_type: Optional[int] = None
    smvs_billing_type: Optional[int] = None
    smvs_payment_type: Optional[int] = None
    
    # Box fields (CMS-1500 form)
    smvs_box1plantype: Optional[int] = None
    smvs_box6patientrelationshiptoinsured: Optional[int] = None
    smvs_box21diagnosisindicator: Optional[str] = None
    smvs_box24ediagnosispointer: Optional[str] = None
    smvs_box26patientsaccountnumber: Optional[str] = None
    smvs_box33billingproviderlastname: Optional[str] = None
    smvs_box33anpi: Optional[str] = None
    
    # Other fields
    smvs_total_days: Optional[int] = None
    smvs_needs_review: Optional[bool] = None
    smvs_is_forwarded_claim: Optional[bool] = None
    
    # Service lines (populated separately)
    service_lines: Optional[List[ServiceLine]] = Field(default_factory=list)
    
    class Config:
        extra = "allow"  # Allow additional fields from Dataverse


# Status code mappings (based on your data)
CLAIM_STATUS_CODES = {
    153940000: "Draft",
    153940001: "Submitted", 
    153940002: "Processing",
    153940003: "Approved",
    153940004: "Rejected",
    153940005: "Paid",
    153940006: "Failed",  # From your example
    153940007: "Pending",
    153940008: "On Hold",
}

INTERNAL_STATE_CODES = {
    153940000: "New",
    153940001: "In Progress",
    153940008: "Error",  # From your example
}


def get_claim_status_name(status_code: Optional[int]) -> str:
    """Get human-readable status name"""
    if status_code is None:
        return "Unknown"
    return CLAIM_STATUS_CODES.get(status_code, f"Status {status_code}")


def is_claim_failed(claim: Claim) -> bool:
    """Check if claim has failed"""
    # Check status codes that indicate failure
    if claim.smvs_claimstatus == 153940006:  # Failed status
        return True
    if claim.smvs_internal_state == 153940008:  # Error state
        return True
    # Check for error descriptions or remarks indicating failure
    if claim.smvs_error_description:
        return True
    if claim.smvs_remark and "fail" in claim.smvs_remark.lower():
        return True
    return False

"""
Dataverse Service Line Models
Defines the structure of service lines from Dataverse.
"""
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class ServiceLine(BaseModel):
    """Service line entity from Dataverse with complete field mapping"""
    
    # Core identifiers
    smvs_servicelineid: Optional[str] = Field(None, description="Unique service line ID")
    smvs_name: Optional[str] = Field(None, description="Service line name")
    smvs_serviceline_control_number: Optional[str] = Field(None, description="Service line control number")
    
    # Claim references
    smvs_claimid_value: Optional[str] = Field(None, alias="_smvs_claimid_value", description="Related claim ID")
    smvs_ncpdpclaimid: Optional[str] = Field(None, description="NCPDP claim ID")
    
    # Procedure and service codes
    smvs_proceduresservicesorsupplies: Optional[str] = Field(None, description="CPT/HCPCS procedure code")
    smvs_cpt_hcpcs_code_value: Optional[str] = Field(None, alias="_smvs_cpt_hcpcs_code_value", description="CPT/HCPCS code lookup reference")
    smvs_product_service_id: Optional[str] = Field(None, description="Product/service ID")
    smvs_product_service_id_qualifier: Optional[str] = Field(None, description="Product/service ID qualifier")
    
    # Modifiers
    smvs_modifiers: Optional[str] = Field(None, description="Primary modifiers (colon-separated, e.g., 'AA:BB:CC')")
    smvs_additional_modifiers: Optional[str] = Field(None, description="Additional modifiers (colon-separated)")
    
    # Diagnosis pointers
    smvs_diagnosispointer: Optional[str] = Field(None, description="Diagnosis pointer (e.g., '1:2')")
    
    # Financial fields
    smvs_charges: Optional[str] = Field(None, description="Charged amount")
    smvs_expected_amount_service_line: Optional[float] = Field(None, description="Expected amount for service line")
    smvs_expected_amount_service_line_base: Optional[float] = Field(None, description="Base expected amount")
    smvs_other_payer_insurance_paid_amount: Optional[float] = Field(None, description="Other payer paid amount")
    smvs_other_payer_insurance_paid_amount_base: Optional[float] = Field(None, description="Base other payer amount")
    
    # Date fields
    smvs_datesofservice: Optional[str] = Field(None, description="Service date (from)")
    smvs_dateofserviceto: Optional[str] = Field(None, description="Service date (to)")
    smvs_other_payer_check_processed_date: Optional[str] = Field(None, description="Other payer check date")
    
    # Place of service
    smvs_placeofservice: Optional[int] = Field(None, description="Place of service code (e.g., 11=Office, 12=Home)")
    smvs_place_of_service_experimental: Optional[str] = Field(None, description="Experimental place of service")
    
    # Units and measurements
    smvs_dayorunitvalue: Optional[str] = Field(None, description="Days or units value")
    smvs_daysorunits: Optional[int] = Field(None, description="Days or units code")
    smvs_product_service_unit_count: Optional[str] = Field(None, description="Product/service unit count")
    smvs_product_service_unit_measurement_code: Optional[str] = Field(None, description="Unit measurement code")
    smvs_unitmeasurementcode: Optional[str] = Field(None, description="Unit measurement code")
    
    # NDC (National Drug Code) fields
    smvs_nationaldrugcode: Optional[str] = Field(None, description="National Drug Code")
    smvs_ndc_number: Optional[str] = Field(None, description="NDC number")
    smvs_nationaldrugunitcount: Optional[str] = Field(None, description="NDC unit count")
    smvs_ndc_code_key_value: Optional[str] = Field(None, alias="_smvs_ndc_code_key_value", description="NDC code key reference")
    
    # Provider information
    smvs_renderingproviderid: Optional[str] = Field(None, description="Rendering provider ID")
    smvs_renderingprovidernpi: Optional[str] = Field(None, description="Rendering provider NPI")
    smvs_rendering_provider_value: Optional[str] = Field(None, alias="_smvs_rendering_provider_value", description="Rendering provider lookup")
    smvs_idqualifier: Optional[str] = Field(None, description="ID qualifier")
    
    # Authorization and additional info
    smvs_prior_authorization_number: Optional[str] = Field(None, description="Prior authorization number")
    smvs_prior_authorization_id_value: Optional[str] = Field(None, alias="_smvs_prior_authorization_id_value", description="Prior authorization ID reference")
    smvs_additional_service_line_information: Optional[str] = Field(None, description="Additional information")
    
    # Vaccine fields
    smvs_vaccine_key_value: Optional[str] = Field(None, alias="_smvs_vaccine_key_value", description="Vaccine key reference")
    
    # Status and flags
    statuscode: Optional[int] = Field(None, description="Status code")
    statecode: Optional[int] = Field(None, description="State code (0=Active, 1=Inactive)")
    smvs_isactive: Optional[bool] = Field(None, description="Is active flag")
    smvs_ignoreforclaimsubmission: Optional[bool] = Field(None, description="Ignore for claim submission")
    
    # Additional fields
    smvs_emg: Optional[str] = Field(None, description="Emergency indicator")
    smvs_epsdtorfamilyplan: Optional[str] = Field(None, description="EPSDT or family plan indicator")
    smvs_order: Optional[int] = Field(None, description="Line order")
    
    # Audit fields
    createdon: Optional[str] = Field(None, description="Created date")
    modifiedon: Optional[str] = Field(None, description="Modified date")
    createdby_value: Optional[str] = Field(None, alias="_createdby_value", description="Created by user ID")
    modifiedby_value: Optional[str] = Field(None, alias="_modifiedby_value", description="Modified by user ID")
    createdonbehalfby_value: Optional[str] = Field(None, alias="_createdonbehalfby_value", description="Created on behalf of user ID")
    modifiedonbehalfby_value: Optional[str] = Field(None, alias="_modifiedonbehalfby_value", description="Modified on behalf of user ID")
    
    # Ownership fields
    ownerid_value: Optional[str] = Field(None, alias="_ownerid_value", description="Owner ID")
    owninguser_value: Optional[str] = Field(None, alias="_owninguser_value", description="Owning user ID")
    owningteam_value: Optional[str] = Field(None, alias="_owningteam_value", description="Owning team ID")
    owningbusinessunit_value: Optional[str] = Field(None, alias="_owningbusinessunit_value", description="Owning business unit ID")
    
    # Currency and exchange
    transactioncurrencyid_value: Optional[str] = Field(None, alias="_transactioncurrencyid_value", description="Transaction currency ID")
    exchangerate: Optional[float] = Field(None, description="Exchange rate")
    
    # Import and versioning
    importsequencenumber: Optional[int] = Field(None, description="Import sequence number")
    overriddencreatedon: Optional[str] = Field(None, description="Overridden created on date")
    timezoneruleversionnumber: Optional[int] = Field(None, description="Timezone rule version")
    utcconversiontimezonecode: Optional[int] = Field(None, description="UTC conversion timezone code")
    versionnumber: Optional[int] = Field(None, description="Version number")
    
    # OData metadata
    odata_etag: Optional[str] = Field(None, alias="@odata.etag", description="OData ETag")
    
    class Config:
        extra = "allow"  # Allow additional fields from Dataverse
        populate_by_name = True  # Allow field population by alias


# Place of Service code mappings
PLACE_OF_SERVICE_CODES = {
    11: "Office",
    12: "Home",
    21: "Inpatient Hospital",
    22: "On Campus-Outpatient Hospital",
    23: "Emergency Room - Hospital",
    24: "Ambulatory Surgical Center",
    31: "Skilled Nursing Facility",
    32: "Nursing Facility",
    33: "Custodial Care Facility",
    41: "Ambulance - Land",
    42: "Ambulance - Air or Water",
    49: "Independent Clinic",
    50: "Federally Qualified Health Center",
    51: "Inpatient Psychiatric Facility",
    52: "Psychiatric Facility-Partial Hospitalization",
    53: "Community Mental Health Center",
    54: "Intermediate Care Facility/Individuals with Intellectual Disabilities",
    55: "Residential Substance Abuse Treatment Facility",
    56: "Psychiatric Residential Treatment Center",
    57: "Non-residential Substance Abuse Treatment Facility",
    60: "Mass Immunization Center",
    61: "Comprehensive Inpatient Rehabilitation Facility",
    62: "Comprehensive Outpatient Rehabilitation Facility",
    65: "End-Stage Renal Disease Treatment Facility",
    71: "Public Health Clinic",
    72: "Rural Health Clinic",
    81: "Independent Laboratory",
    99: "Other Place of Service",
}


# Days or Units code mappings
DAYS_OR_UNITS_CODES = {
    153940000: "Days",
    153940001: "Units",
}


def get_place_of_service_name(pos_code: Optional[int]) -> str:
    """Get human-readable place of service name"""
    if pos_code is None:
        return "Unknown"
    return PLACE_OF_SERVICE_CODES.get(pos_code, f"POS {pos_code}")


def parse_modifiers(modifiers: Optional[str]) -> List[str]:
    """Parse colon-separated modifiers into a list"""
    if not modifiers:
        return []
    return [m.strip() for m in modifiers.split(":") if m.strip()]


def parse_diagnosis_pointers(diagnosis_pointer: Optional[str]) -> List[int]:
    """Parse diagnosis pointer string into list of integers (e.g., '1:2' -> [1, 2])"""
    if not diagnosis_pointer:
        return []
    try:
        return [int(p.strip()) for p in diagnosis_pointer.split(":") if p.strip()]
    except ValueError:
        return []


def get_all_modifiers(service_line: ServiceLine) -> List[str]:
    """Get all modifiers combined from primary and additional modifier fields"""
    all_mods = []
    if service_line.smvs_modifiers:
        all_mods.extend(parse_modifiers(service_line.smvs_modifiers))
    if service_line.smvs_additional_modifiers:
        all_mods.extend(parse_modifiers(service_line.smvs_additional_modifiers))
    return all_mods


def get_service_date_range(service_line: ServiceLine) -> tuple[Optional[str], Optional[str]]:
    """Get service date range (from_date, to_date)"""
    return (service_line.smvs_datesofservice, service_line.smvs_dateofserviceto)


def is_service_line_active(service_line: ServiceLine) -> bool:
    """Check if service line is active and not ignored"""
    if service_line.statecode == 1:  # Inactive
        return False
    if service_line.smvs_ignoreforclaimsubmission:
        return False
    if not service_line.smvs_isactive:
        return False
    return True


def format_service_line_display(service_line: ServiceLine) -> str:
    """Format service line for display"""
    parts = []
    
    if service_line.smvs_proceduresservicesorsupplies:
        parts.append(f"Code: {service_line.smvs_proceduresservicesorsupplies}")
    
    if service_line.smvs_charges:
        parts.append(f"Charges: ${service_line.smvs_charges}")
    
    if service_line.smvs_dayorunitvalue:
        parts.append(f"Units: {service_line.smvs_dayorunitvalue}")
    
    modifiers = get_all_modifiers(service_line)
    if modifiers:
        parts.append(f"Modifiers: {', '.join(modifiers)}")
    
    return " | ".join(parts)

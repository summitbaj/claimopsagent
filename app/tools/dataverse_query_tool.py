
from langchain.tools import tool
from pydantic import BaseModel, Field
from typing import Optional
from app.dataverse.client import DataverseClient


class ClaimByIdInput(BaseModel):
    self: object
    claim_id: str = Field(..., description="Claim ID (GUID) to fetch.")
    token: str


class HistoricalClaimsInput(BaseModel):
    self: object
    filter_xml: Optional[str] = Field('', description="Additional FetchXML filter XML (e.g., <filter>...</filter>)")
    token: str


class ServiceLinesByClaimInput(BaseModel):
    self: object
    claim_id: str = Field(..., description="Claim ID (GUID) to fetch service lines for.")
    token: str




@tool("get_claim_by_id", args_schema=ClaimByIdInput)
def get_claim_by_id(self: object, claim_id: str, token: str) -> list:
    """
    Fetch a specific claim by ID using FetchXML via DataverseClient.
    """
    client = DataverseClient(token=token)
    return client.get_claim_by_id(self, claim_id)




@tool("get_historical_claims", args_schema=HistoricalClaimsInput)
def get_historical_claims(self: object, filter_xml: Optional[str] = '', token: str = None) -> list:
    """
    Fetch historical claims using FetchXML and optional filter via DataverseClient.
    """
    client = DataverseClient(token=token)
    return client.get_historical_claims(self, filter_xml=filter_xml)




@tool("get_service_lines_by_claim", args_schema=ServiceLinesByClaimInput)
def get_service_lines_by_claim(self: object, claim_id: str, token: str) -> list:
    """
    Fetch service lines for a specific claim using FetchXML via DataverseClient.
    """
    client = DataverseClient(token=token)
    return client.get_service_lines_by_claim(self, claim_id)

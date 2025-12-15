
from langchain.tools import tool
from pydantic import BaseModel, Field
from typing import Optional, List
from app.dataverse.client import DataverseClient


# Input schemas without 'self' or 'token' - these are provided by the factory
class ClaimByIdInput(BaseModel):
    claim_id: str = Field(..., description="Claim ID (GUID) to fetch.")


class HistoricalClaimsInput(BaseModel):
    filter_xml: Optional[str] = Field('', description="Additional FetchXML filter XML (e.g., <filter>...</filter>)")


class ServiceLinesByClaimInput(BaseModel):
    claim_id: str = Field(..., description="Claim ID (GUID) to fetch service lines for.")


def create_dataverse_tools(token: Optional[str] = None) -> List:
    """
    Create Dataverse query tools with the MSAL token bound from the agent context.
    This allows the tools to authenticate with Dataverse using the user's token.
    
    Args:
        token: MSAL access token from frontend authentication
        
    Returns:
        List of tools that can query Dataverse with the bound token
    """
    
    @tool("get_claim_by_id", args_schema=ClaimByIdInput)
    def get_claim_by_id(claim_id: str) -> list:
        """
        Fetch a specific claim by ID using FetchXML via DataverseClient.
        Uses the authenticated user's token to access Dataverse.
        """
        try:
            client = DataverseClient(token=token)
            return client.get_claim_by_id(claim_id)
        except Exception as e:
            return [f"Error fetching claim: {str(e)}"]

    @tool("get_historical_claims", args_schema=HistoricalClaimsInput)
    def get_historical_claims(filter_xml: Optional[str] = '') -> list:
        """
        Fetch historical claims using FetchXML and optional filter via DataverseClient.
        Uses the authenticated user's token to access Dataverse.
        """
        try:
            client = DataverseClient(token=token)
            return client.get_historical_claims(filter_xml=filter_xml)
        except Exception as e:
            return [f"Error fetching historical claims: {str(e)}"]

    @tool("get_service_lines_by_claim", args_schema=ServiceLinesByClaimInput)
    def get_service_lines_by_claim(claim_id: str) -> list:
        """
        Fetch service lines for a specific claim using FetchXML via DataverseClient.
        Uses the authenticated user's token to access Dataverse.
        """
        try:
            client = DataverseClient(token=token)
            return client.get_service_lines_by_claim(claim_id)
        except Exception as e:
            return [f"Error fetching service lines: {str(e)}"]
    
    return [get_claim_by_id, get_historical_claims, get_service_lines_by_claim]

from typing import List, Dict, Optional
from langchain_core.tools import tool
from app.dataverse.client import DataverseClient

client = DataverseClient()

@tool
def fetch_recent_claims(status: str = "Failed", limit: int = 5) -> List[Dict]:
    """
    Fetches recent healthcare claims from Dataverse, optionally filtered by status.
    Useful for finding examples of failed claims or analyzing trends.
    """
    # Map friendly status to OData if needed, or passes raw
    # Example: smvs_status eq 123456 (just assuming string for now)
    filter_query = f"smvs_statusname eq '{status}'" if status else ""
    return client.fetch_claims(filter_query=filter_query, top=limit)

@tool
def head_claim_details(claim_id: str) -> Dict:
    """
    Retrieves full details for a specific claim, including its service lines.
    Use this when you need deep context on a single claim.
    """
    # 1. Get Claim
    claims = client.fetch_claims(filter_query=f"smvs_claimid eq {claim_id}", top=1)
    if not claims:
        return {"error": "Claim not found"}
    
    claim = claims[0]
    
    # 2. Get Lines
    lines = client.fetch_service_lines(claim_id)
    claim["service_lines"] = lines
    return claim

@tool
def update_claim_modifiers(service_line_id: str, modifiers: str) -> str:
    """
    Updates the procedure modifiers for a specific service line.
    Use this to apply corrections (e.g. adding 'GW' or 'KX').
    """
    success = client.update_service_line(service_line_id, {"smvs_modifiers": modifiers})
    if success:
        return f"Successfully updated service line {service_line_id} with modifiers: {modifiers}"
    else:
        return f"Failed to update service line {service_line_id}"

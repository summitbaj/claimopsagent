import requests
import time
from typing import Optional, Dict, Any, List
from azure.identity import DefaultAzureCredential, InteractiveBrowserCredential
from azure.core.exceptions import ClientAuthenticationError
from app.core.config import settings
from app.dataverse.mock import get_mock_claims, get_mock_service_lines


class DataverseClient:
    def __init__(self, token: Optional[str] = None):
        self.base_url = settings.DATAVERSE_URL.rstrip('/')
        self.token = token # User-provided token (via MSAL)
        self.token_expiry = 0
        self.credential = None

    def _get_token(self) -> str:
        """Retrieves OAuth2 token."""
        # 0. Use explicitly provided token (from Frontend MSAL)
        if self.token:
            return self.token
        if self.token and time.time() < self.token_expiry:
            return self.token

        scope = f"{self.base_url}/.default"
        
        try:
            # 1. Try Default Credential (Env Vars -> Managed Identity -> VS Code -> Azure CLI)
            if not self.credential:
                self.credential = DefaultAzureCredential(exclude_interactive_browser_credential=False)
            
            access_token = self.credential.get_token(scope)
            self.token = access_token.token
            self.token_expiry = access_token.expires_on
            return self.token
            
        except ClientAuthenticationError:
            print("⚠️ Default Auth failed. Trying Interactive Browser Login...")
            try:
                # 2. Fallback to Interactive Browser
                self.credential = InteractiveBrowserCredential()
                access_token = self.credential.get_token(scope)
                self.token = access_token.token
                self.token_expiry = access_token.expires_on
                return self.token
            except Exception as e:
                print(f"❌ Interactive Auth Failed: {e}")
                
        except Exception as e:
            print(f"❌ Auth Failed: {e}")
            if "dummy" in self.base_url:
                 print("⚠️ Using Mock Token for dummy URL.")
                 return "mock_token"
        
        return "mock_token"
    
    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self._get_token()}",
            "Content-Type": "application/json",
            "OData-MaxVersion": "4.0",
            "OData-Version": "4.0",
            "Prefer": "odata.include-annotations=\"*\""
        }
    
    def fetchxml_query(self, fetchxml: str, entity: str, token: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Generic method to query Dataverse using FetchXML.
        Args:
            fetchxml: The FetchXML string
            entity: The entity logical name (e.g., 'smvs_claims', 'smvs_servicelines')
            token: Optional access token (overrides client token)
        Returns:
            List of records (dicts)
        """
        import logging
        logger = logging.getLogger("dataverse_fetchxml_tool")
        url = f"{self.base_url}/api/data/v9.2/{entity}"
        logger.debug(f"[FetchXMLTool] FetchXML: {fetchxml[:100]}...")
        response = requests.get(url, headers=self._headers(), params={"fetchXml": fetchxml})
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            logger.error(f"[FetchXMLTool] HTTP error: {e} | Response: {response.text}")
            raise
        return response.json().get("value", [])


    def _map_status_codes(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Helper to map integer status codes to string labels."""
        from app.core.constants import CLAIM_STATUS, CLAIM_TYPE
        
        if "smvs_claimstatus" in record:
            code = record["smvs_claimstatus"]
            # Check if it's already mapped (in case of double processing) or string
            if isinstance(code, int):
                 record["smvs_claimstatus"] = CLAIM_STATUS.get(code, code)
        
        if "smvs_claim_type" in record:
             code = record["smvs_claim_type"]
             if isinstance(code, int):
                 record["smvs_claim_type_code"] = code # Keep code
                 record["smvs_claim_type"] = CLAIM_TYPE.get(code, code)
                 
        return record

    def get_claim_by_id(self, claim_id: str, access_token: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch a specific claim by ID using FetchXML.
        """
        from app.dataverse.fetchxml_templates import FETCHXML_CLAIM
        filter_xml = f'<filter type="and"><condition attribute="smvs_claimid" operator="eq" value="{claim_id}" /></filter>'
        fetchxml = FETCHXML_CLAIM.format(filter=filter_xml)
        results = self.fetchxml_query(fetchxml, "smvs_claims", token=access_token)
        # Force label mapping
        return [self._map_status_codes(r) for r in results]

    def get_historical_claims(self, filter_xml: str = '', access_token: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch historical claims using FetchXML and optional filter.
        """
        from app.dataverse.fetchxml_templates import FETCHXML_HISTORICAL_CLAIMS
        from app.core.constants import CLAIM_TYPE
        
        # Auto-correct string labels to IDs in filter
        name_to_id = {v: k for k, v in CLAIM_TYPE.items()}
        for label, code in name_to_id.items():
            if f"value='{label}'" in filter_xml:
                filter_xml = filter_xml.replace(f"value='{label}'", f"value='{code}'")
            if f'value="{label}"' in filter_xml:
                filter_xml = filter_xml.replace(f'value="{label}"', f'value="{code}"')
                
        fetchxml = FETCHXML_HISTORICAL_CLAIMS.format(filter=filter_xml)
        results = self.fetchxml_query(fetchxml, "smvs_claims", token=access_token)
        return [self._map_status_codes(r) for r in results]

    def get_service_lines_by_claim(self, claim_id: str, access_token: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch service lines for a specific claim using FetchXML.
        """
        from app.dataverse.fetchxml_templates import FETCHXML_SERVICE_LINES
        fetchxml = FETCHXML_SERVICE_LINES.format(claim_id=claim_id)
        return self.fetchxml_query(fetchxml, "smvs_servicelines", token=access_token)
    

    def update_service_line(self, line_id: str, updates: Dict[str, Any]) -> bool:
        """
        Updates a service line entity.
        
        Args:
            line_id: The service line ID (GUID)
            updates: Dictionary of fields to update
            
        Returns:
            True if update was successful, False otherwise
        """
        endpoint = f"{self.base_url}/api/data/v9.2/smvs_servicelines({line_id})"
        
        try:
            print(f"------------ DATAVERSE UPDATE ------------")
            print(f"PATCH {endpoint}")
            print(f"Payload: {updates}")
            
            if settings.MOCK_MODE:
                print(f"[MOCK] Updated {line_id} with {updates}")
                print(f"-------------------------------------------")
                return True
            
            response = requests.patch(endpoint, headers=self._headers(), json=updates)
            print(f"Response Status: {response.status_code}")
            print(f"-------------------------------------------")
            
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Error updating line {line_id}: {e}")
            print(f"-------------------------------------------")
            return False

    def update_claim(self, claim_id: str, updates: Dict[str, Any]) -> bool:
        """
        Updates a claim entity.
        
        Args:
            claim_id: The claim ID (GUID)
            updates: Dictionary of fields to update
            
        Returns:
            True if update was successful, False otherwise
        """
        endpoint = f"{self.base_url}/api/data/v9.2/smvs_claims({claim_id})"
        
        try:
            print(f"------------ DATAVERSE UPDATE ------------")
            print(f"PATCH {endpoint}")
            print(f"Payload: {updates}")
            
            if settings.MOCK_MODE:
                print(f"[MOCK] Updated claim {claim_id} with {updates}")
                print(f"-------------------------------------------")
                return True
            
            response = requests.patch(endpoint, headers=self._headers(), json=updates)
            print(f"Response Status: {response.status_code}")
            print(f"-------------------------------------------")
            
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Error updating claim {claim_id}: {e}")
            print(f"-------------------------------------------")
            return False
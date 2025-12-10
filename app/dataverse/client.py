import requests
import time
from typing import Optional, Dict, Any, List
from azure.identity import DefaultAzureCredential, InteractiveBrowserCredential
from azure.core.exceptions import ClientAuthenticationError
from app.core.config import settings

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

    def fetch_claims(self, filter_query: str = "", top: int = 10) -> List[Dict[str, Any]]:
        """Fetches claims from smvs_claims."""
        endpoint = f"{self.base_url}/api/data/v9.2/smvs_claims"
        params = {"$top": top}
        if filter_query:
            params["$filter"] = filter_query
        
        params["$select"] = "smvs_claimid,smvs_name,smvs_totalamount,smvs_status,smvs_failurereason,smvs_remark"

        try:
            print(f"------------ DATAVERSE REQUEST ------------")
            print(f"GET {endpoint}")
            print(f"Params: {params}")
            print(f"Token present: {'Yes' if self.token else 'No'}")
            
            if settings.MOCK_MODE:
                print("Mock mode active. Returning user provided claim.")
                return [{
                    "smvs_claimid": "41807965-3611-f011-9988-000d3a30044f",
                    "smvs_name": "Claim for Delivery Managemenr Test",
                    "smvs_totalamount": 0,
                    "smvs_status": 153940019,
                    "smvs_failurereason": "Populate Service Line Failed",
                    "smvs_remark": None
                }] 
            
            response = requests.get(endpoint, headers=self._headers(), params=params)
            
            print(f"Response Status: {response.status_code}")
            if response.status_code != 200:
                print(f"Response Body: {response.text}")
            else:
                data = response.json()
                count = len(data.get("value", []))
                print(f"Fetched {count} claims.")
            print(f"-------------------------------------------")

            response.raise_for_status()
            return response.json().get("value", [])
        except Exception as e:
            print(f"Error fetching claims: {e}")
            return []

    def fetch_service_lines(self, claim_id: str) -> List[Dict[str, Any]]:
        """Fetches lines for a specific claim."""
        endpoint = f"{self.base_url}/api/data/v9.2/smvs_servicelines"
        params = {
            "$filter": f"_smvs_claim_value eq {claim_id}",
            "$select": "smvs_servicelineid,smvs_name,smvs_procedurecode,smvs_modifiers,smvs_lineamount"
        }
        try:
             print(f"------------ DATAVERSE REQUEST ------------")
             print(f"GET {endpoint}")
             print(f"Params: {params}")

             if settings.MOCK_MODE:
                return []
             response = requests.get(endpoint, headers=self._headers(), params=params)
             
             print(f"Response Status: {response.status_code}")
             print(f"-------------------------------------------")

             response.raise_for_status()
             return response.json().get("value", [])
        except Exception as e:
            print(f"Error fetching lines: {e}")
            return []

    def update_service_line(self, line_id: str, updates: Dict[str, Any]) -> bool:
        """Updates a service line entity."""
        endpoint = f"{self.base_url}/api/data/v9.2/smvs_servicelines({line_id})"
        try:
             print(f"------------ DATAVERSE UPDATE ------------")
             print(f"PATCH {endpoint}")
             print(f"Payload: {updates}")

             if settings.MOCK_MODE:
                print(f"[MOCK] Updated {line_id} with {updates}")
                return True
             
             response = requests.patch(endpoint, headers=self._headers(), json=updates)
             print(f"Response Status: {response.status_code}")
             print(f"-------------------------------------------")
             
             response.raise_for_status()
             return True
        except Exception as e:
            print(f"Error updating line {line_id}: {e}")
            return False

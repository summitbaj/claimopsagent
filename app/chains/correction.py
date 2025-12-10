from typing import Dict, List, Any
import uuid
from app.engine.rules_engine import RulesEngine
from app.dataverse.client import DataverseClient

class CorrectionChain:
    def __init__(self, token: str = None):
        self.engine = RulesEngine()
        self.dv_client = DataverseClient(token=token)


    def _is_uuid(self, val):
        try:
            uuid.UUID(str(val))
            return True
        except ValueError:
            return False

    def process_claim(self, claim_id: str) -> Dict[str, Any]:
        """
        Evaluates and applies corrections for a claim.
        """
        # 1. Fetch Claim
        if self._is_uuid(claim_id):
            query = f"smvs_claimid eq {claim_id}"
        else:
            query = f"smvs_claimid eq '{claim_id}'"

        claims = self.dv_client.fetch_claims(query, top=1)
        if not claims:
            return {"error": "Claim not found", "applied_corrections": []}
        
        claim = claims[0]
        
        # 2. Evaluate Rules
        matched_rules = self.engine.evaluate(claim)
        
        results = []
        
        # 3. Apply Actions
        for rule in matched_rules:
            action = rule.action
            
            if action.target_entity == "smvs_servicelines":
                # Fetch lines
                lines = self.dv_client.fetch_service_lines(claim_id)
                for line in lines:
                    success = self.dv_client.update_service_line(
                        line["smvs_servicelineid"],
                        {action.update_field: action.value}
                    )
                    results.append({
                        "rule_id": rule.id,
                        "target": line["smvs_servicelineid"],
                        "status": "Applied" if success else "Failed",
                        "description": rule.description
                    })
            
            # Add other entity types logic here if needed
            
        return {
            "claim_id": claim_id,
            "matched_rules_count": len(matched_rules),
            "applied_corrections": results
        }

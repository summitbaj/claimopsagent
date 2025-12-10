from typing import Dict, Any, List
import uuid
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

from app.core.config import settings
from app.dataverse.client import DataverseClient

class PredictionResult(BaseModel):
    prediction: str = Field(description="FAIL or PASS")
    confidence_score: float = Field(description="Between 0.0 and 1.0")
    top_reasons: List[str] = Field(description="List of reasons for the prediction")
    similar_claim_ids: List[str] = Field(description="IDs of historical claims used for context")

class PredictionChain:
    def __init__(self, token: str = None):
        self.llm = ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model="gpt-4.1-nano",
            temperature=0
        )
        self.client = DataverseClient(token=token)

    def _get_similar_claims(self, claim_data: Dict) -> List[Dict]:
        """
        Mock retrieval of similar historical claims.
        In prod, this would embed the claim_data and query Chroma/FAISS.
        """
        # Mock context 
        return [
            {"smvs_claimid": "H-1001", "outcome": "FAIL", "reason": "Missing Modifier GW for Hospice"},
            {"smvs_claimid": "H-1002", "outcome": "PASS", "reason": "Correct Modifier Applied"}
        ]


    def _is_uuid(self, val):
        try:
            uuid.UUID(str(val))
            return True
        except ValueError:
            return False

    def predict(self, claim_id: str) -> Dict[str, Any]:
        """
        Predicts if a claim will fail based on similar historical claims.
        """
        # Mock mode: Return mock prediction without calling OpenAI
        if settings.MOCK_MODE:
            print("🎭 Mock mode: Returning mock prediction")
            return {
                "prediction": "FAIL",
                "confidence_score": 0.85,
                "top_reasons": [
                    "Missing required modifier GW for Hospice service",
                    "Service line population failed",
                    "Potential billing code mismatch"
                ],
                "similar_claim_ids": ["H-1001", "H-1002"]
            }
        
        # 1. Fetch live claim data
        if self._is_uuid(claim_id):
            query = f"smvs_claimid eq {claim_id}"
        else:
            query = f"smvs_claimid eq '{claim_id}'"
            
        claims = self.client.fetch_claims(query, top=1)
        if not claims:
            return {"error": "Claim not found"}
        
        claim = claims[0]
        # Fetch lines for detail
        lines = self.client.fetch_service_lines(claim_id)
        claim["service_lines"] = lines

        # 2. Retrieve context (RAG)
        similar_claims = self._get_similar_claims(claim)

        # 3. Construct Prompt
        parser = JsonOutputParser(pydantic_object=PredictionResult)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert Healthcare Claims Analyst. Predict if the following claim will FAIL or PASS based on the provided similar historical claims context. Return valid JSON."),
            ("user", """
            Current Claim Candidate:
            {claim_data}

            Similar Historical Claims (Context):
            {context}

            Provide your prediction, confidence, top contributing reasons, and cite the similar claim IDs used.
            
            {format_instructions}
            """)
        ])

        chain = prompt | self.llm | parser

        # 4. Invoke
        result = chain.invoke({
            "claim_data": str(claim),
            "context": str(similar_claims),
            "format_instructions": parser.get_format_instructions()
        })
        
        return result

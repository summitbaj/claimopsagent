# app/chains/prediction.py
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field
import json
from app.core.config import settings
from app.tools.dataverse_query_tool import get_claim_by_id, get_historical_claims, get_service_lines_by_claim
from app.dataverse.schema_reference import dataverse_schema
from fastapi import HTTPException

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
        # Provide only the new FetchXML-based tools to the agent
        self.tools = [get_claim_by_id, get_historical_claims, get_service_lines_by_claim]
        self.agent = create_react_agent(self.llm, self.tools)
        self.token = token  # Store the token

    async def predict(self, claim_id: str) -> Dict[str, Any]:
        """
        Predicts if a claim will fail based on similar historical claims using the FetchXML-based tools.
        """
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

        def build_schema_prompt():
            lines = ["Available Dataverse tables and fields:"]
            for table, fields in dataverse_schema.items():
                lines.append(f"- {table}: {', '.join(fields)}")
            return "\n".join(lines)

        schema_prompt = build_schema_prompt()
        messages = [
            SystemMessage(content=f"""You are an expert Healthcare Claims Analyst working with Microsoft Dataverse.
You have direct access to the Dataverse schema below. Use only the provided table and field names when using the available tools: get_claim_by_id, get_historical_claims, get_service_lines_by_claim.

{schema_prompt}
"""),
            HumanMessage(content=f"""Analyze claim with ID: {claim_id}

WORKFLOW:
1. Use the get_claim_by_id tool to query the primary claim using the correct table and column names from the schema above.
2. Use the get_historical_claims tool to query similar historical claims (e.g., failed claims) using the schema above.
3. (Optional) Use get_service_lines_by_claim to fetch service lines for the claim if needed.
4. Analyze the patterns and make your prediction.

Return your final answer as a JSON object:
{{
    "prediction": "FAIL" or "PASS",
    "confidence_score": 0.0 to 1.0,
    "top_reasons": ["reason 1", "reason 2", "reason 3"],
    "similar_claim_ids": ["id1", "id2", "id3"]
}}

The claim ID you're analyzing is: {claim_id}
""")
        ]

        # Invoke the agent
        result = await self.agent.ainvoke(
            {"messages": messages, "self": self, "token": self.token},
            config={"configurable": {"thread_id": claim_id}}
        )

        # Extract the final message
        final_message = result["messages"][-1].content

        # Parse the JSON response
        try:
            parsed_result = json.loads(final_message)
            return parsed_result
        except Exception:
            # Check for token or credential errors in the LLM output
            if "token" in final_message.lower() or "credential" in final_message.lower():
                raise HTTPException(status_code=401, detail="Token missing or invalid for Dataverse access.")
            # Otherwise, return a generic error
            raise HTTPException(status_code=500, detail=f"LLM output not JSON: {final_message}")
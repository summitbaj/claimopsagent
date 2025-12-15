# app/chains/prediction.py
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field
import json
from app.core.config import settings
from app.tools.dataverse_query_tool import create_dataverse_tools
from app.dataverse.schema_reference import dataverse_schema
from fastapi import HTTPException

class PredictionResult(BaseModel):
    prediction: str = Field(description="FAIL or PASS")
    confidence_score: float = Field(description="Between 0.0 and 1.0")
    top_reasons: List[str] = Field(description="List of reasons for the prediction")
    similar_claim_ids: List[str] = Field(description="IDs of historical claims used for context")

class PredictionChain:
    def __init__(self, token: str = None):
        if settings.LLM_PROVIDER.lower() == "groq":
            print(f"🚀 Using LLM Provider: GROQ ({settings.GROQ_MODEL})")
            self.llm = ChatOpenAI(
                api_key=settings.GROQ_API_KEY,
                base_url=settings.GROQ_API_URL,
                model=settings.GROQ_MODEL,
                temperature=0
            )
        else:
            print(f"🚀 Using LLM Provider: OPENAI ({settings.OPENAI_MODEL})")
            self.llm = ChatOpenAI(
                api_key=settings.OPENAI_API_KEY,
                model=settings.OPENAI_MODEL,
                temperature=0
            )
        self.token = token
        # Create tools with MSAL token bound from frontend authentication
        self.tools = create_dataverse_tools(token=token)
        self.agent = create_react_agent(self.llm, self.tools)

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
            from app.core.constants import CLAIM_STATUS, CLAIM_TYPE
            lines = ["Available Dataverse tables and fields:"]
            for table, fields in dataverse_schema.items():
                lines.append(f"- {table}: {', '.join(fields)}")
            
            lines.append("\nReference Codes (Use Integers for Filtering):")
            lines.append("CLAIM_STATUS:")
            for code, label in CLAIM_STATUS.items():
                lines.append(f"  {label}: {code}")
            
            lines.append("CLAIM_TYPE:")
            for code, label in CLAIM_TYPE.items():
                lines.append(f"  {label}: {code}")
                
            return "\n".join(lines)

        schema_prompt = build_schema_prompt()
        messages = [
            SystemMessage(content=f"""You are an expert Healthcare Claims Analyst working with Microsoft Dataverse.
You have direct access to the Dataverse schema below. Use only the provided table and field names when using the available tools: get_claim_by_id, get_historical_claims, get_service_lines_by_claim.

{schema_prompt}

CRITICAL INSTRUCTIONS:
1. **Check Status First**: If the claim's 'smvs_claimstatus' is 153940008 (BILL_PAID), STOP analysis. prediction="PASS", confidence=1.0. Rationale: "Claim is already fully paid."
2. **Translate Labels to Codes**: `get_claim_by_id` returns human-readable LABELS (e.g., "NCPDP Claim"). When querying `get_historical_claims`, you MUST translate these back to INTEGERS using the Reference Codes above (e.g., use 916310002, NOT "NCPDP Claim").
3. **Contextual Analysis**: When finding similar historical failures, consider that old errors might have been fixed in the system. Don't assume past failures imply current failure if recent claims are passing.
4. **Chain of Thought**: You must document your thinking process step-by-step.
"""),
            HumanMessage(content=f"""Analyze claim with ID: {claim_id}

WORKFLOW:
1. Use get_claim_by_id to fetch the claim. Check status immediately.
2. If not paid, use get_service_lines_by_claim to get line items.
3. Use get_historical_claims to find patterns (e.g. failures for same Payer or CPT).
4. Analyze findings. explicitly considering if past errors are relevant.

Return your final answer as a JSON object:
{{
    "prediction": "FAIL" or "PASS",
    "confidence_score": 0.0 to 1.0,
    "top_reasons": ["reason 1", "reason 2"],
    "similar_claim_ids": ["id1", "id2"],
    "reasoning_trace": [
        "Step 1: Analyzed claim status...",
        "Step 2: Checked payer rules...",
        "Step 3: Compared with 5 historical claims..."
    ],
    "rationale": "Detailed explanation of why you reached this conclusion, referencing specific data points.",
    "limitations": "Mention if historical data is old or if errors might be fixed."
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
        
        # Clean markdown if present
        clean_message = final_message.strip()
        
        # Robust extraction: Look for markdown code blocks first
        import re
        json_block_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", clean_message, re.DOTALL)
        if json_block_match:
            clean_message = json_block_match.group(1)
        else:
            # Fallback: look for the first '{' and last '}'
            start_idx = clean_message.find('{')
            end_idx = clean_message.rfind('}')
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                clean_message = clean_message[start_idx : end_idx + 1]
        
        clean_message = clean_message.strip()

        # Parse the JSON response
        try:
            parsed_result = json.loads(clean_message)
            
            # --- Extract raw data from tool outputs ---
            claim_details = {}
            service_lines = []
            similar_claims = []
            
            for msg in result.get("messages", []):
                # Check for ToolMessage (has 'name' attribute in some versions, or check type)
                if msg.type == 'tool':
                    try:
                        data = json.loads(msg.content)
                        if msg.name == "get_claim_by_id":
                            if isinstance(data, list) and len(data) > 0:
                                claim_details = data[0]
                        elif msg.name == "get_service_lines_by_claim":
                            service_lines = data
                        elif msg.name == "get_historical_claims":
                            similar_claims = data
                    except:
                        continue

            # Fallback: If service lines are missing (e.g. Agent stopped early due to PAID status),
            # manually fetch them for display purposes.
            if not service_lines:
                try:
                    # Find the tool
                    for tool in self.tools:
                        if tool.name == "get_service_lines_by_claim":
                            print(f"🔧 Manually fetching service lines for {claim_id}...")
                            service_lines = tool.invoke(claim_id)
                            parsed_result["service_lines"] = service_lines
                            break
                except Exception as e:
                    print(f"⚠️ Failed to manually fetch service lines: {e}")

            # Add to result
            parsed_result["claim_details"] = claim_details
            parsed_result["service_lines"] = service_lines
            parsed_result["similar_claims_data"] = similar_claims
            
            return parsed_result
        except Exception as e:
            # Check for token or credential errors in the LLM output
            if "token" in final_message.lower() or "credential" in final_message.lower():
                raise HTTPException(status_code=401, detail="Token missing or invalid for Dataverse access.")
            
            # Fallback: Treat the parsing error or non-JSON output as a failed prediction attempt
            # instead of crashing the server. Return the raw message as rationale.
            print(f"⚠️ JSON Parsing failed in prediction.py. Fallback to raw text.\nError: {e}\nContent: {final_message}")
            
            return {
                "prediction": "FAIL", 
                "confidence_score": 0.0,
                "top_reasons": ["AI Response Formatting Error"],
                "similar_claim_ids": [],
                "reasoning_trace": ["AI failed to return structured JSON."],
                "rationale": f"The AI could not generate a valid analysis. Raw Output: {final_message}",
                "limitations": "Output format error.",
                "claim_details": {},
                "service_lines": [],
                "similar_claims_data": []
            }
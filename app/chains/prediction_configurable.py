"""
Configurable Prediction Chain with User-Defined Criteria
Allows users to specify custom prediction criteria and similarity rules
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
import json

from app.core.config import settings

from app.models.claim import Claim
from app.models.service_line import ServiceLine, format_service_line_display


class UserCriteria(BaseModel):
    """User-defined prediction criteria"""
    focus_areas: List[str] = Field(
        description="What to focus on (e.g., 'procedure codes', 'modifiers', 'amounts', 'diagnosis')",
        default=["procedure codes", "modifiers", "amounts"]
    )
    similarity_rules: str = Field(
        description="How to define similar claims",
        default="Same status and similar amount range (+/- 50%)"
    )
    risk_factors: List[str] = Field(
        description="Specific things to check for failure risk",
        default=["missing modifiers", "invalid procedure codes", "amount thresholds"]
    )
    comparison_context: str = Field(
        description="Additional context for comparison",
        default="Compare with claims from last 30 days"
    )


class DetailedPredictionResult(BaseModel):
    """Enhanced prediction result with detailed analysis"""
    prediction: str = Field(description="FAIL or PASS")
    confidence_score: float = Field(description="0.0 to 1.0")
    
    # Detailed reasoning
    top_reasons: List[str] = Field(description="Reasons for prediction")
    risk_factors_found: List[Dict[str, Any]] = Field(description="Specific risk factors identified")
    
    # Comparison data
    similar_claims: List[Dict[str, Any]] = Field(description="Similar claims with details")
    similarity_explanation: str = Field(description="Why these claims are similar")
    
    # User criteria application
    criteria_applied: Dict[str, Any] = Field(description="How user criteria was used")
    focus_areas_analyzed: List[Dict[str, str]] = Field(description="Analysis per focus area")


class ConfigurablePredictionChain:
    """
    Advanced prediction chain that uses user-defined criteria
    """
    
    def __init__(self, token: str = None):
        self.llm = ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model="gpt-4o",
            temperature=0
        )
        self.token = token
    
    def predict_with_criteria(
        self, 
        claim_id: str, 
        user_criteria: Optional[UserCriteria] = None
    ) -> Dict[str, Any]:
        """
        Predict claim outcome using user-defined criteria
        
        Args:
            claim_id: The claim ID to analyze
            user_criteria: Optional user-defined criteria for prediction
            
        Returns:
            Detailed prediction result
        """
        if settings.MOCK_MODE:
            return self._mock_prediction(user_criteria)
        
        # Use default criteria if none provided
        if user_criteria is None:
            user_criteria = UserCriteria()
        
        try:
            # Step 1: Fetch target claim with full details
            print(f"📋 Fetching claim: {claim_id}")
            target_claim = self._fetch_claim_with_details(claim_id)
            
            # Step 2: AI constructs similarity query based on user criteria
            print(f"🔍 Finding similar claims based on criteria...")
            similar_claims = self._find_similar_claims_ai(target_claim, user_criteria)
            
            # Step 3: Detailed comparison and prediction
            print(f"🤖 Analyzing with user criteria...")
            prediction = self._analyze_with_criteria(
                target_claim, 
                similar_claims, 
                user_criteria
            )
            
            return prediction
            
        except Exception as e:
            return {
                "error": f"Prediction failed: {str(e)}",
                "prediction": "ERROR",
                "confidence_score": 0.0
            }
    
    def _fetch_claim_with_details(self, claim_id: str) -> Dict[str, Any]:
        """Fetch claim and its service lines"""
        # Fetch main claim record
        claim_json = fetch_dataverse_record("smvs_claim", claim_id)
        claim_data = json.loads(claim_json) if isinstance(claim_json, str) else claim_json
        
        if "error" in claim_data:
            raise Exception(f"Claim not found: {claim_id}")
        
        # Fetch service lines
        service_lines_json = query_dataverse_service_lines(claim_id)
        service_lines_data = json.loads(service_lines_json) if isinstance(service_lines_json, str) else service_lines_json
        service_lines = service_lines_data if isinstance(service_lines_data, list) else []
        
        # Parse service lines with detailed model
        parsed_lines = []
        for line in service_lines:
            try:
                sl = ServiceLine(**line)
                parsed_lines.append({
                    "id": sl.smvs_servicelineid,
                    "procedure_code": sl.smvs_proceduresservicesorsupplies,
                    "modifiers": sl.smvs_modifiers,
                    "additional_modifiers": sl.smvs_additional_modifiers,
                    "charges": sl.smvs_charges,
                    "diagnosis_pointer": sl.smvs_diagnosispointer,
                    "place_of_service": sl.smvs_placeofservice,
                    "units": sl.smvs_dayorunitvalue,
                    "display": format_service_line_display(sl)
                })
            except Exception:
                continue
        
        claim_data["service_lines"] = parsed_lines
        claim_data["service_lines_count"] = len(parsed_lines)
        
        return claim_data
    
    def _find_similar_claims_ai(
        self, 
        target_claim: Dict[str, Any], 
        criteria: UserCriteria
    ) -> List[Dict[str, Any]]:
        """Use AI to find similar claims based on user criteria"""
        
        # Build natural language query incorporating user criteria
        query_builder_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a healthcare claims analyst. Based on the target claim and user criteria, 
            construct a natural language query to find similar historical claims.
            
            Focus on what the user wants to compare. Be specific about:
            - Status/state to match
            - Amount ranges
            - Time periods
            - Any specific risk factors mentioned
            
            Output ONLY the natural language query, nothing else."""),
            ("user", """Target Claim:
- Claim ID: {claim_id}
- Status: {status}
- Amount: {amount}
- Service Lines: {service_lines_count}
- Procedure Codes: {procedures}

User Criteria:
- Focus Areas: {focus_areas}
- Similarity Rules: {similarity_rules}
- Comparison Context: {comparison_context}

Generate a query to find similar historical claims.""")
        ])
        
        # Extract procedure codes from service lines
        procedures = [
            line.get("procedure_code") 
            for line in target_claim.get("service_lines", [])
            if line.get("procedure_code")
        ]
        
        chain = query_builder_prompt | self.llm
        response = chain.invoke({
            "claim_id": target_claim.get("smvs_claimid"),
            "status": target_claim.get("smvs_claimstatus"),
            "amount": target_claim.get("smvs_claimed_amount", 0),
            "service_lines_count": target_claim.get("service_lines_count", 0),
            "procedures": ", ".join(procedures[:3]),  # First 3 codes
            "focus_areas": ", ".join(criteria.focus_areas),
            "similarity_rules": criteria.similarity_rules,
            "comparison_context": criteria.comparison_context
        })
        
        query_text = response.content.strip()
        print(f"  📝 Query: {query_text}")
        
        # Execute AI-powered query
        result_json = query_dataverse_claims_ai(query_text, limit=5)

        # Normalize result to Python object
        if isinstance(result_json, (dict, list)):
            result = result_json
        elif isinstance(result_json, str):
            try:
                result = json.loads(result_json)
            except json.JSONDecodeError:
                raise ValueError(f"AI returned non-JSON response: {result_json}")
        else:
            raise ValueError(f"Unexpected result type from AI query: {type(result_json)}")

        similar_claims = result.get("claims", []) if isinstance(result, dict) else (result if isinstance(result, list) else [])
        
        # Enrich with service lines
        enriched_claims = []
        for claim in similar_claims:
            if claim.get("smvs_claimid") == target_claim.get("smvs_claimid"):
                continue
            
            # Fetch service lines for similar claim
            try:
                lines_json = query_dataverse_service_lines(claim.get("smvs_claimid"))
                lines_data = json.loads(lines_json) if isinstance(lines_json, str) else lines_json
                claim["service_lines"] = lines_data if isinstance(lines_data, list) else []
            except Exception:
                claim["service_lines"] = []
            
            enriched_claims.append(claim)
        
        return enriched_claims
    
    def _analyze_with_criteria(
        self,
        target_claim: Dict[str, Any],
        similar_claims: List[Dict[str, Any]],
        criteria: UserCriteria
    ) -> Dict[str, Any]:
        """Perform detailed analysis using user criteria"""
        
        parser = JsonOutputParser(pydantic_object=DetailedPredictionResult)
        
        analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert healthcare claims analyst. Analyze the target claim and predict if it will FAIL or PASS.

Use the user-defined criteria to guide your analysis:
1. Focus on the specified areas
2. Apply the similarity rules to understand context
3. Check for the specified risk factors
4. Compare based on the user's context requirements

Provide detailed reasoning including:
- Why you made this prediction
- What risk factors you found
- How similar claims performed and why they're similar
- How you applied each focus area

Return valid JSON matching the schema."""),
            ("user", """TARGET CLAIM:
{target_claim}

SIMILAR HISTORICAL CLAIMS:
{similar_claims}

USER CRITERIA:
- Focus Areas: {focus_areas}
- Similarity Rules: {similarity_rules}
- Risk Factors to Check: {risk_factors}
- Comparison Context: {comparison_context}

Analyze and predict: FAIL or PASS

{format_instructions}""")
        ])
        
        chain = analysis_prompt | self.llm | parser
        
        result = chain.invoke({
            "target_claim": json.dumps(target_claim, indent=2),
            "similar_claims": json.dumps(similar_claims, indent=2),
            "focus_areas": ", ".join(criteria.focus_areas),
            "similarity_rules": criteria.similarity_rules,
            "risk_factors": ", ".join(criteria.risk_factors),
            "comparison_context": criteria.comparison_context,
            "format_instructions": parser.get_format_instructions()
        })
        
        return result
    
    def _mock_prediction(self, criteria: Optional[UserCriteria]) -> Dict[str, Any]:
        """Mock response for testing"""
        return {
            "prediction": "FAIL",
            "confidence_score": 0.87,
            "top_reasons": [
                "Missing modifier GW required for hospice",
                "Similar claims with same procedure failed 3/5 times",
                "Amount exceeds typical range by 45%"
            ],
            "risk_factors_found": [
                {"factor": "Missing Modifier", "severity": "HIGH", "details": "GW modifier required but not present"},
                {"factor": "Amount Outlier", "severity": "MEDIUM", "details": "45% above average"}
            ],
            "similar_claims": [
                {
                    "claim_id": "abc-123",
                    "outcome": "FAIL",
                    "similarity_score": 0.92,
                    "reason": "Same procedure code, similar amount"
                }
            ],
            "similarity_explanation": "Found claims with matching procedure codes and amounts within 50% range",
            "criteria_applied": {
                "focus_areas": criteria.focus_areas if criteria else ["default"],
                "similarity_rules": criteria.similarity_rules if criteria else "default"
            },
            "focus_areas_analyzed": [
                {"area": "Procedure Codes", "finding": "90677 found in 3 failed claims"},
                {"area": "Modifiers", "finding": "Missing GW modifier"}
            ]
        }

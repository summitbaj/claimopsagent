from fastapi import FastAPI, HTTPException, Header, Depends
import json
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from typing_extensions import Annotated
import logging

from app.core.telemetry import setup_telemetry
from app.chains.prediction import PredictionChain
from app.chains.prediction_configurable import ConfigurablePredictionChain, UserCriteria
from app.chains.guidance import GuidanceChain
from app.chains.correction import CorrectionChain
from app.chains.analytics import AnalyticsChain
from app.dataverse.mcp_runner import ensure_loop, run_sync
from app.dataverse.mcp_client import get_mcp_client

# Setup Telemetry on startup
setup_telemetry()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Debug: Check MOCK_MODE setting on startup
from app.core.config import settings
logger.info(f"🔧 MOCK_MODE is set to: {settings.MOCK_MODE}")

app = FastAPI(title="Claims Intelligence Agent API")

# CORS for React app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict to UI domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models ---
class PredictRequest(BaseModel):
    claim_id: str

class ConfigurablePredictRequest(BaseModel):
    claim_id: str
    focus_areas: Optional[List[str]] = ["procedure codes", "modifiers", "amounts"]
    similarity_rules: Optional[str] = "Same status and similar amount range (+/- 50%)"
    risk_factors: Optional[List[str]] = ["missing modifiers", "invalid procedure codes", "amount thresholds"]
    comparison_context: Optional[str] = "Compare with claims from last 30 days"

class GuidanceRequest(BaseModel):
    query: str

class CorrectionRequest(BaseModel):
    claim_id: str

# --- Helper ---
def get_token(authorization: Annotated[Optional[str], Header()] = None) -> Optional[str]:
    if authorization and authorization.startswith("Bearer "):
        return authorization.split(" ")[1]
    return None

# --- Endpoints ---

@app.get("/health")
def health_check():
    logger.info("[HEALTH] Health check endpoint called")
    return {"status": "ok"}


@app.post("/predict")
async def predict_claim(req: PredictRequest, token: str = Depends(get_token)):
    """Predicts claim outcome. Set use_agent=true to use AI-powered query agent."""
    logger.info(f"[PREDICT] Request received for claim_id: {req.claim_id}")
    logger.info(f"[PREDICT] Token present: {token is not None}")
    try:
        logger.info("[PREDICT] Creating PredictionChain...")
        chain = PredictionChain(token=token)
        
        logger.info("[PREDICT] Calling chain.predict()...")
        result = await chain.predict(req.claim_id)
        logger.info(f"[PREDICT] Result received: {result}")
        if "error" in result:
             raise HTTPException(status_code=404, detail=result["error"])
        logger.info("[PREDICT] Returning successful result")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[PREDICT] Error occurred: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict-agent")
def predict_claim_agent(req: PredictRequest, token: str = Depends(get_token)):
    """Predicts claim outcome using AI agent that dynamically queries Dataverse."""
    logger.info(f"[PREDICT-AGENT] Request received for claim_id: {req.claim_id}")
    logger.info(f"[PREDICT-AGENT] Token present: {token is not None}")
    try:
        logger.info("[PREDICT-AGENT] Agent endpoint now uses PredictionChain implementation")
        chain = PredictionChain(token=token)
        logger.info("[PREDICT-AGENT] Calling chain.predict()...")
        result = chain.predict(req.claim_id)
        logger.info(f"[PREDICT-AGENT] Result received: {result}")
        if "error" in result:
             raise HTTPException(status_code=404, detail=result["error"])
        logger.info("[PREDICT-AGENT] Returning successful result")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[PREDICT-AGENT] Error occurred: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict-custom")
def predict_claim_custom(req: ConfigurablePredictRequest, token: str = Depends(get_token)):
    """
    Predicts claim outcome using user-defined criteria.
    Allows customization of similarity rules, focus areas, and risk factors.
    """
    logger.info(f"[PREDICT-CUSTOM] Request received for claim_id: {req.claim_id}")
    logger.info(f"[PREDICT-CUSTOM] Focus areas: {req.focus_areas}")
    logger.info(f"[PREDICT-CUSTOM] Similarity rules: {req.similarity_rules}")
    
    try:
        # Create user criteria from request
        criteria = UserCriteria(
            focus_areas=req.focus_areas,
            similarity_rules=req.similarity_rules,
            risk_factors=req.risk_factors,
            comparison_context=req.comparison_context
        )
        
        logger.info("[PREDICT-CUSTOM] Creating ConfigurablePredictionChain...")
        chain = ConfigurablePredictionChain(token=token)
        
        logger.info("[PREDICT-CUSTOM] Executing prediction with custom criteria...")
        result = chain.predict_with_criteria(req.claim_id, criteria)
        
        logger.info(f"[PREDICT-CUSTOM] Prediction: {result.get('prediction', 'UNKNOWN')}")
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        return result
        
    except Exception as e:
        logger.error(f"[PREDICT-CUSTOM] Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/guide")
def get_guidance(req: GuidanceRequest):
    """Gets billing SOP guidance. (No Dataverse auth needed for SOPs usually, but adding for consistency if needed later)"""
    try:
        chain = GuidanceChain()
        response = chain.get_guidance(req.query)
        return {"guidance": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/correct")
def apply_correction(req: CorrectionRequest, token: str = Depends(get_token)):
    """Applies rule-based corrections."""
    try:
        chain = CorrectionChain(token=token)
        result = chain.process_claim(req.claim_id)
        if "error" in result:
             raise HTTPException(status_code=404, detail=result["error"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analyze")
def get_analytics(token: str = Depends(get_token)):
    """Generates analytics report and charts."""
    try:
        chain = AnalyticsChain(token=token)
        result = chain.generate_report()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/debug/get-claim/{claim_id}")
def debug_get_claim(claim_id: str):
    """Debug helper: call MCP client's get_claim_by_id and return raw MCP response."""
    try:
        logger.info(f"[DEBUG] get_claim_by_id called for {claim_id}")
        mcp = get_mcp_client()
        from app.dataverse.mcp_runner import run_sync
        rows = run_sync(mcp.get_claim_by_id(claim_id), timeout=30)
        return {"rows": rows}
    except Exception as e:
        logger.exception("[DEBUG] Error calling get_claim_by_id")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/debug/describe/{table_name}")
def debug_describe_table(table_name: str):
    try:
        logger.info(f"[DEBUG] describe_table called for {table_name}")
        mcp = get_mcp_client()
        from app.dataverse.mcp_runner import run_sync
        desc = run_sync(mcp._call_tool('describe_table', arguments={'table_name': table_name}, expect_list=False), timeout=30)
        return {"description": desc}
    except Exception as e:
        logger.exception("[DEBUG] Error calling describe_table")
        raise HTTPException(status_code=500, detail=str(e))
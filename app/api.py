# --- PYDANTIC V2 COMPATIBILITY PATCH START ---
from app.core.patch_chromadb import apply_chromadb_patch
apply_chromadb_patch()
# --- PYDANTIC V2 COMPATIBILITY PATCH END ---

# Load environment variables first (including LANGSMITH_API_KEY)
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Header, Depends, UploadFile, File
import json
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from typing_extensions import Annotated
import logging
import shutil
from pathlib import Path

from app.core.telemetry import setup_telemetry
from app.chains.prediction import PredictionChain
from app.chains.prediction_configurable import ConfigurablePredictionChain, UserCriteria
from app.chains.guidance import GuidanceChain
from app.chains.correction import CorrectionChain
from app.chains.analytics import AnalyticsChain
from app.chains.chat_agent import ChatAgent
from app.chains.agent_types import ChatRequest
from app.core.knowledge_base import KnowledgeBase
from langsmith import Client, wrappers

# Setup Telemetry on startup
setup_telemetry()

# LangSmith tracing is automatically enabled via environment variables:
# - LANGCHAIN_TRACING_V2=true
# - LANGSMITH_API_KEY=your-key
# No additional code needed for automatic tracing of all LangChain chains

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Debug: Check MOCK_MODE setting on startup
from app.core.config import settings
import os
logger.info(f"🔧 MOCK_MODE is set to: {settings.MOCK_MODE}")
logger.info(f"🔍 LangSmith Tracing: {os.getenv('LANGCHAIN_TRACING_V2', 'false')}")
logger.info(f"🔑 LangSmith API Key: {'✓ Set' if os.getenv('LANGSMITH_API_KEY') else '✗ Not Set'}")

app = FastAPI(title="Claims Intelligence Agent API")

@app.on_event("startup")
async def startup_event():
    from app.core.auto_ingest import run_auto_ingest
    logger.info("🚀 Starting ClaimsOps Agent...")
    run_auto_ingest()

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
def get_analytics(
    start_date: Optional[str] = None, 
    end_date: Optional[str] = None, 
    force_refresh: bool = False,
    token: str = Depends(get_token)
):
    """Generates analytics report and charts."""
    try:
        chain = AnalyticsChain(token=token)
        result = chain.generate_report(start_date=start_date, end_date=end_date, force_refresh=force_refresh)
        return result
    except Exception as e:
        logger.error(f"[ANALYTICS] Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat_query(req: ChatRequest, token: str = Depends(get_token)):
    """
    Multi-role chat endpoint that routes queries to appropriate tools.
    Supports knowledge base, claim analysis, and reporting.
    """
    logger.info(f"[CHAT] Query received: {req.query[:100]}...")
    try:
        agent = ChatAgent(token=token)
        result = await agent.process_query(req.query, req.history)
        return result
    except Exception as e:
        logger.error(f"[CHAT] Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingest")
async def ingest_file(file: UploadFile = File(...)):
    """
    Ingest a file (PowerPoint, PDF, or Word) into the knowledge base.
    """
    logger.info(f"[INGEST] File upload: {file.filename}")
    
    # Validate file type
    allowed_extensions = ('.pptx', '.ppt', '.pdf', '.docx', '.doc')
    if not file.filename.endswith(allowed_extensions):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    try:
        # Create uploads directory
        upload_dir = Path("data/uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Save file
        file_path = upload_dir / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"[INGEST] File saved to: {file_path}")
        
        # Ingest into knowledge base
        kb = KnowledgeBase()
        result = kb.ingest_file(str(file_path))
        
        return result
        
    except Exception as e:
        logger.error(f"[INGEST] Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/knowledge-sources")
def get_knowledge_sources():
    """Get list of all uploaded knowledge sources."""
    try:
        kb = KnowledgeBase()
        sources = kb.get_uploaded_sources()
        return {"sources": sources}
    except Exception as e:
        logger.error(f"[KNOWLEDGE-SOURCES] Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/knowledge-sources/{filename}")
def delete_knowledge_source(filename: str):
    """Delete a knowledge source."""
    try:
        kb = KnowledgeBase()
        result = kb.delete_source(filename)
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DELETE-SOURCE] Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/knowledge-stats")
def get_knowledge_stats():
    """Get statistics about the knowledge base."""
    try:
        kb = KnowledgeBase()
        return kb.get_collection_stats()
    except Exception as e:
        logger.error(f"[KNOWLEDGE-STATS] Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))



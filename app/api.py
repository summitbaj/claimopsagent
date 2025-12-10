from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from typing_extensions import Annotated

from app.core.telemetry import setup_telemetry
from app.chains.prediction import PredictionChain
from app.chains.guidance import GuidanceChain
from app.chains.correction import CorrectionChain
from app.chains.analytics import AnalyticsChain

# Setup Telemetry on startup
setup_telemetry()

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
    return {"status": "ok"}

@app.post("/predict")
def predict_claim(req: PredictRequest, token: str = Depends(get_token)):
    """Predicts claim outcome."""
    try:
        chain = PredictionChain(token=token)
        result = chain.predict(req.claim_id)
        if "error" in result:
             raise HTTPException(status_code=404, detail=result["error"])
        return result
    except Exception as e:
        print(e)
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

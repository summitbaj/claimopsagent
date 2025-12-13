import json
from pathlib import Path
from typing import Any, Dict

_DATA_PATH = Path(__file__).parent / "mock_data.json"

def load_mock_data() -> Dict[str, Any]:
    if not _DATA_PATH.exists():
        return {"claims": [], "service_lines": []}
    with open(_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def get_mock_claims(limit: int = 10):
    data = load_mock_data()
    return data.get("claims", [])[:limit]

def get_mock_service_lines(claim_id: str):
    data = load_mock_data()
    lines = [l for l in data.get("service_lines", []) if l.get("_smvs_claimid_value") == claim_id]
    return lines

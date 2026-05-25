from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel

from api.dependencies import get_current_user
from db.user import User
from api.xai.explainer import default_explainer

router = APIRouter()

class ExplainRequest(BaseModel):
    texts: List[str]

@router.post("/explain", response_model=List[Dict[str, Any]])
def explain_texts(
    request: ExplainRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Generate explainability (XAI) scores for given texts using SHAP.
    """
    if not request.texts:
        raise HTTPException(status_code=400, detail="No texts provided.")
    
    results = default_explainer.explain(request.texts)
    return results

import json
from pathlib import Path
from fastapi import APIRouter

router = APIRouter(prefix="/api/model", tags=["model"])
META_PATH = Path(__file__).resolve().parents[1] / "ml" / "models" / "metrics.json"


@router.get("/metrics")
def metrics():
    if not META_PATH.exists():
        return {
            "detail": "Model not trained yet",
            "disclaimer": "Model metrics are based on the synthetic demonstration dataset.",
        }
    with open(META_PATH) as f:
        meta = json.load(f)
    return {
        **meta,
        "disclaimer": (
            "Model metrics are based on the synthetic demonstration dataset "
            "and should not be interpreted as production validation. "
            "Predictions are estimates that support, not replace, administrative judgment."
        ),
    }


@router.get("/features")
def features():
    if not META_PATH.exists():
        return {"features": [], "importance": {}}
    with open(META_PATH) as f:
        meta = json.load(f)
    return {
        "features": meta.get("feature_names", []),
        "importance": meta.get("feature_importance", {}),
        "n_features": meta.get("n_features"),
    }

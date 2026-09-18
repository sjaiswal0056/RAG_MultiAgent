from __future__ import annotations

import uuid
import logging
import time

from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.dependencies import get_workflow
from app.models.claim import ClaimCase
from app.models.decision import ClaimDecision
from app.graph.workflow import ClaimWorkflow


router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "policy-aware-claim-engine"}


@router.post("/analyze", response_model=ClaimDecision)
def analyze(case: ClaimCase, request: Request, workflow: ClaimWorkflow = Depends(get_workflow)) -> ClaimDecision:
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    started = time.perf_counter()
    logger.info("claim analysis started", extra={"request_id": request_id, "case_id": case.case_id, "workflow_node": "api"})
    try:
        result = workflow.analyze(case)
        logger.info("claim analysis completed", extra={"request_id": request_id, "case_id": case.case_id,
            "workflow_node": "api", "elapsed_ms": (time.perf_counter() - started) * 1000})
        return result
    except FileNotFoundError as exc:
        logger.exception("policy resource unavailable", extra={"request_id": request_id, "case_id": case.case_id,
            "workflow_node": "api", "exception_category": type(exc).__name__})
        raise HTTPException(status_code=503, detail={"request_id": request_id, "error": str(exc)}) from exc
    except RuntimeError as exc:
        logger.exception("analysis runtime failure", extra={"request_id": request_id, "case_id": case.case_id,
            "workflow_node": "api", "exception_category": type(exc).__name__})
        raise HTTPException(status_code=503, detail={"request_id": request_id, "error": str(exc)}) from exc

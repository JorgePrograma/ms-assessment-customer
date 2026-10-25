from fastapi import APIRouter

from app.presentation.dtos import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> HealthResponse:
    return HealthResponse()

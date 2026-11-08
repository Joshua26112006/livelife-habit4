"""Optional. A demo that needs a backend defines a FastAPI `router`; it is mounted at /demo-livelife/<folder>/api/."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/ping")
def ping():
    return {"message": "hello"}

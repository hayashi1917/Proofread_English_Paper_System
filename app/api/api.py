from fastapi import APIRouter
from app.api.routes.analyze_document import router as analyze_document_router

api_router = APIRouter()

api_router.include_router(analyze_document_router)


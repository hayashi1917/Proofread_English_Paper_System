from fastapi import APIRouter
from app.api.routes.analyze_document import router as analyze_document_router
from app.api.routes.knowledge_pipeline import router as knowledge_pipeline_router

api_router = APIRouter()

api_router.include_router(analyze_document_router)
api_router.include_router(knowledge_pipeline_router)


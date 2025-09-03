from fastapi import APIRouter
from app.api.routes.analyze_document import router as analyze_document_router
from app.api.routes.knowledge_pipeline import router as knowledge_pipeline_router
from app.api.routes.store_and_search_db import router as store_and_search_db_router
from app.api.routes.proofread_english_paper import router as proofread_english_paper_router

api_router = APIRouter()

api_router.include_router(analyze_document_router)
api_router.include_router(knowledge_pipeline_router)
api_router.include_router(store_and_search_db_router)
api_router.include_router(proofread_english_paper_router)

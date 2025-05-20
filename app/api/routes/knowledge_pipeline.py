from fastapi import APIRouter, UploadFile, File
from app.services.execute_knowledge_pipeline import execute_knowledge_pipeline_batch

router = APIRouter(
    prefix="/knowledge_pipeline",
    tags=["knowledge_pipeline"],
)

@router.post("/")
async def execute_knowledge_pipeline_api():
    return execute_knowledge_pipeline_batch()
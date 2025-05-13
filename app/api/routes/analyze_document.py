from fastapi import APIRouter, UploadFile, File
from app.services.analyze_document_process import analyze_document_process, structure_markdown

router = APIRouter(
    prefix="/analyze_document",
    tags=["analyze_document"],
)

@router.post("/")
async def analyze_document(file: UploadFile = File(...)):
    return await analyze_document_process(file)

@router.post("/structure_result")
async def structure_result(file: UploadFile = File(...)):
    result_dict = await analyze_document_process(file)
    return await structure_markdown(result_dict)


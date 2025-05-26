from fastapi import APIRouter, UploadFile, File
from app.services.proofread_english_paper import proofread_english_paper

router = APIRouter(
    prefix="/proofread_english_paper",
    tags=["proofread_english_paper"],
)
@router.post("/")
async def proofread_english_paper_api():
    """
    校正前の英語論文を校正するAPIエンドポイント
    """
    return proofread_english_paper()
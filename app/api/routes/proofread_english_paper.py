from fastapi import APIRouter, UploadFile, File
from app.services.proofreading.proofread_english_paper import proofread_english_paper, proofread_english_paper_posted_file, proofread_english_paper_without_knowledge

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

@router.post("/file")
async def proofread_english_paper_file_api(file: UploadFile = File(...)):
    """
    校正前の英語論文ファイルを受け取り、校正するAPIエンドポイント
    """
    # ファイルを一時的に保存する処理を追加することも可能
    # ここでは、ファイルの内容を直接処理する例を示す
    file_content = await file.read()
    file_content = file_content.decode("utf-8")  # ファイル内容を文字列に変換
    return proofread_english_paper_posted_file(file_content)

@router.post("/without_knowledge")
async def proofread_english_paper_without_knowledge_api(file: UploadFile = File(...)):
    """
    校正前の英語論文ファイルを受け取り、校正するAPIエンドポイント
    """
    file_content = await file.read()
    file_content = file_content.decode("utf-8")  # ファイル内容を文字列に変換
    return proofread_english_paper_without_knowledge(file_content)
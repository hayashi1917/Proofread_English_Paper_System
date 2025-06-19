from fastapi import APIRouter, UploadFile, File, Query
from typing import Optional
from app.services.proofreading.proofread_english_paper import proofread_english_paper, proofread_english_paper_posted_file, proofread_english_paper_without_knowledge, EnglishPaperProofreadingService
from app.services.knowledge.chunking_file import split_latex_by_command, split_latex_by_sentence, split_latex_by_hybrid, split_latex_by_recursive_nlp
from app.services.proofreading.config.proofreading_paper_config import SplitMode

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

@router.post("/split_by_command")
async def split_latex_by_command_api(file: UploadFile = File(...)):
    """
    LaTeXファイルをコマンド単位で分割して返すAPIエンドポイント
    """
    file_content = await file.read()
    file_content = file_content.decode("utf-8")
    chunks = split_latex_by_command(file_content)
    return {
        "split_type": "command",
        "total_chunks": len(chunks),
        "chunks": chunks
    }

@router.post("/split_by_sentence")
async def split_latex_by_sentence_api(file: UploadFile = File(...)):
    """
    LaTeXファイルを文単位で分割して返すAPIエンドポイント
    """
    file_content = await file.read()
    file_content = file_content.decode("utf-8")
    chunks = split_latex_by_sentence(file_content)
    return {
        "split_type": "sentence",
        "total_chunks": len(chunks),
        "chunks": chunks
    }

@router.post("/split_by_hybrid")
async def split_latex_by_hybrid_api(file: UploadFile = File(...)):
    """
    LaTeXファイルをハイブリッド分割（プリアンブル:コマンド単位、本文:文単位）して返すAPIエンドポイント
    """
    file_content = await file.read()
    file_content = file_content.decode("utf-8")
    chunks = split_latex_by_hybrid(file_content)
    return {
        "split_type": "hybrid",
        "total_chunks": len(chunks),
        "chunks": chunks
    }

@router.post("/proofreading_with_split_mode")
async def proofreading_with_split_mode_api(
    file: UploadFile = File(...),
    split_mode: Optional[str] = Query(SplitMode.SECTION, description="分割モード (section, command, sentence, hybrid)"),
    use_knowledge: Optional[bool] = Query(True, description="知識ベースを使用するかどうか")
):
    """
    LaTeXファイルを指定した分割モードで校正するAPIエンドポイント
    """
    file_content = await file.read()
    file_content = file_content.decode("utf-8")
    
    service = EnglishPaperProofreadingService()
    results = service.proofread_with_options(
        tex_file=file_content,
        use_google_drive=False,
        use_knowledge=use_knowledge,
        split_mode=split_mode
    )
    
    return {
        "split_mode": split_mode,
        "use_knowledge": use_knowledge,
        "total_results": len(results),
        "results": results
    }

@router.post("/split_by_recursive_nlp")
async def split_latex_by_recursive_nlp_api(file: UploadFile = File(...)):
    """
    LaTeXファイルをLangChain RecursiveCharacterTextSplitterで高性能分割するAPIエンドポイント
    """
    file_content = await file.read()
    file_content = file_content.decode("utf-8")
    chunks = split_latex_by_recursive_nlp(file_content)
    return {
        "split_type": "recursive_nlp",
        "total_chunks": len(chunks),
        "chunks": chunks
    }
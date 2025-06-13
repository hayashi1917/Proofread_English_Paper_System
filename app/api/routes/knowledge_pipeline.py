from fastapi import APIRouter, UploadFile, File
from app.services.execute_knowledge_pipeline import execute_knowledge_pipeline_batch, execute_knowledge_pipeline_from_pdf_batch
from libs.azure_client import AzureDocumentIntelligenceClient

router = APIRouter(
    prefix="/knowledge_pipeline",
    tags=["knowledge_pipeline"],
)

@router.post("/")
async def execute_knowledge_pipeline_api():
    return execute_knowledge_pipeline_batch()


@router.post("/from_pdf")
def execute_knowledge_pipeline_from_pdf_api(pdf_folder_id: str = None):
    """
    Google DriveからPDFファイルを取得してナレッジを抽出するAPIエンドポイント
    
    Args:
        pdf_folder_id: Google DriveのPDFフォルダID（オプション）
        
    Returns:
        抽出されたナレッジのリスト
    """
    knowledge_list = execute_knowledge_pipeline_from_pdf_batch(pdf_folder_id)
    return {
        "message": "PDFからのナレッジ抽出が完了しました",
        "knowledge_count": len(knowledge_list),
        "knowledge_list": knowledge_list
    }


@router.get("/cache/stats")
def get_cache_stats():
    """
    Document Intelligence キャッシュの統計情報を取得
    """
    azure_client = AzureDocumentIntelligenceClient()
    return azure_client.get_cache_stats()


@router.get("/cache/files")
def list_cached_files():
    """
    キャッシュされたファイルの一覧を取得
    """
    azure_client = AzureDocumentIntelligenceClient()
    return {
        "cached_files": azure_client.list_cached_files()
    }


@router.post("/cache/cleanup")
def cleanup_cache(days: int = 30):
    """
    古いキャッシュファイルを削除
    
    Args:
        days: 保持期間（日数、デフォルト30日）
    """
    azure_client = AzureDocumentIntelligenceClient()
    azure_client.cleanup_old_cache(days)
    return {
        "message": f"{days}日より古いキャッシュファイルを削除しました"
    }
from fastapi import APIRouter, UploadFile, File
from app.services.knowledge.execute_knowledge_pipeline import execute_knowledge_pipeline_batch, execute_knowledge_pipeline_from_pdf_batch
from libs.azure_client import AzureDocumentIntelligenceClient

router = APIRouter(
    prefix="/knowledge_pipeline",
    tags=["knowledge_pipeline"],
)

@router.post("/")
async def execute_knowledge_pipeline_api():
    return execute_knowledge_pipeline_batch()


@router.post("/from_pdf")
def execute_knowledge_pipeline_from_pdf_api(pdf_folder_id: str = None, use_page_splitting: bool = True, use_enhanced_cache: bool = True):
    """
    Google DriveからPDFファイルを取得してナレッジを抽出するAPIエンドポイント
    
    Args:
        pdf_folder_id: Google DriveのPDFフォルダID（オプション）
        use_page_splitting: ページ分割処理を使用するかどうか（デフォルト: True）
        use_enhanced_cache: 強化キャッシュシステムを使用するかどうか（デフォルト: True）
        
    Returns:
        抽出されたナレッジのリスト
    """
    knowledge_list = execute_knowledge_pipeline_from_pdf_batch(pdf_folder_id, use_page_splitting, use_enhanced_cache)
    
    if use_enhanced_cache and use_page_splitting:
        processing_method = "強化キャッシュ + ページ分割処理"
    elif use_page_splitting:
        processing_method = "ページ分割処理"
    else:
        processing_method = "従来の処理"
    
    return {
        "message": f"PDFからのナレッジ抽出が完了しました（{processing_method}）",
        "knowledge_count": len(knowledge_list),
        "processing_method": processing_method,
        "cache_enabled": use_enhanced_cache,
        "knowledge_list": knowledge_list
    }





@router.get("/enhanced_cache/stats")
def get_enhanced_cache_stats():
    """
    強化キャッシュシステムの詳細統計情報を取得
    """
    azure_client = AzureDocumentIntelligenceClient(enable_cache=True, use_enhanced_cache=True)
    return azure_client.get_cache_stats()


@router.get("/enhanced_cache/recommendations")
def get_cache_recommendations():
    """
    キャッシュ最適化の推奨事項を取得
    """
    from app.services.knowledge.utils.enhanced_cache_system import EnhancedDocumentIntelligenceCache
    cache = EnhancedDocumentIntelligenceCache()
    return cache.get_cache_recommendations()


@router.post("/enhanced_cache/cleanup")
def cleanup_enhanced_cache(days_old: int = 30, min_access_count: int = 1, max_size_mb: float = None):
    """
    条件に基づく強化キャッシュのクリーンアップ
    
    Args:
        days_old: 削除対象の古さ（日数）
        min_access_count: 最小アクセス回数
        max_size_mb: 最大ファイルサイズ（MB）
    """
    from app.services.knowledge.utils.enhanced_cache_system import EnhancedDocumentIntelligenceCache
    cache = EnhancedDocumentIntelligenceCache()
    removed_count = cache.cleanup_by_criteria(days_old, min_access_count, max_size_mb)
    
    return {
        "message": f"{removed_count}個のキャッシュアイテムを削除しました",
        "removed_count": removed_count,
        "criteria": {
            "days_old": days_old,
            "min_access_count": min_access_count,
            "max_size_mb": max_size_mb
        }
    }


@router.get("/diagnose_folder/{folder_id}")
def diagnose_pdf_folder(folder_id: str):
    """
    Google DriveフォルダのPDF構成を診断する
    
    Args:
        folder_id: Google DriveフォルダID
        
    Returns:
        フォルダ内のファイル詳細情報と診断結果
    """
    from app.services.knowledge.access_google_drive import download_knowledge_pdf_files
    from app.services.shared.logging_utils import log_proofreading_info
    
    try:
        log_proofreading_info(f"[diagnose_pdf_folder] フォルダ診断開始: {folder_id}")
        
        # ファイル取得
        pdf_files = download_knowledge_pdf_files(folder_id)
        
        # 診断情報構築
        diagnosis = {
            "folder_id": folder_id,
            "total_files": len(pdf_files),
            "files": [],
            "analysis": {
                "likely_page_separated": False,
                "single_document": False,
                "recommended_processing": "従来の処理"
            }
        }
        
        page_pattern_count = 0
        for pdf_file in pdf_files:
            file_info = {
                "name": pdf_file["name"],
                "size_bytes": pdf_file["size"],
                "size_mb": round(pdf_file["size"] / (1024 * 1024), 2),
                "is_page_like": "ページ" in pdf_file["name"] or "page" in pdf_file["name"].lower()
            }
            
            if file_info["is_page_like"]:
                page_pattern_count += 1
            
            diagnosis["files"].append(file_info)
        
        # 分析結果
        if len(pdf_files) == 1:
            diagnosis["analysis"]["single_document"] = True
            diagnosis["analysis"]["recommended_processing"] = "ページ分割処理"
        elif page_pattern_count > len(pdf_files) * 0.5:
            diagnosis["analysis"]["likely_page_separated"] = True
            diagnosis["analysis"]["recommended_processing"] = "従来の処理（既にページ分割済み）"
        
        log_proofreading_info(f"[diagnose_pdf_folder] 診断完了: {len(pdf_files)}ファイル")
        
        return diagnosis
        
    except Exception as e:
        return {
            "error": f"フォルダ診断に失敗しました: {e}",
            "folder_id": folder_id
        }
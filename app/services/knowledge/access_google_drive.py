"""
Google Driveファイルアクセスサービス

Google Drive APIを使用してファイルの検索・ダウンロードを行い、
後続の処理（チャンキング、知識抽出等）に必要な形式でデータを提供します。
"""
from typing import List, Dict, Any

from app.services.knowledge.core.google_drive_engine import GoogleDriveEngine
from app.services.shared.logging_utils import log_proofreading_info
from app.services.shared.exceptions import GoogleDriveError


class GoogleDriveService:
    """Google Driveファイルアクセスサービス"""
    
    def __init__(self):
        self.engine = GoogleDriveEngine()
    
    def download_knowledge_tex_files(self, folder_id: str) -> List[Dict[str, Any]]:
        """
        ナレッジ構築用のTeXファイルをダウンロード
        
        Args:
            folder_id (str): Google DriveフォルダID
            
        Returns:
            List[Dict[str, Any]]: ダウンロードしたTeXファイルのリスト
            各ファイルは以下の構造:
            - "id": ファイルID
            - "name": ファイル名
            - "content": ファイル内容（bytes）
            - "knowledge_type": ナレッジタイプ ("学会フォーマット")
            - "mime_type": MIMEタイプ
            - "size": ファイルサイズ
            
        Raises:
            GoogleDriveError: ダウンロードに失敗した場合
        """
        try:
            log_proofreading_info("ナレッジ用TeXファイルダウンロードを開始")
            return self.engine.download_files_from_folder(
                folder_id=folder_id,
                file_type="tex",
                knowledge_type="学会フォーマット"
            )
        except Exception as e:
            raise GoogleDriveError(f"ナレッジ用TeXファイルダウンロードに失敗しました: {e}")
    
    def download_knowledge_pdf_files(self, folder_id: str) -> List[Dict[str, Any]]:
        """
        ナレッジ構築用のPDFファイルをダウンロード
        
        Args:
            folder_id (str): Google DriveフォルダID
            
        Returns:
            List[Dict[str, Any]]: ダウンロードしたPDFファイルのリスト
            各ファイルは以下の構造:
            - "id": ファイルID
            - "name": ファイル名
            - "content": ファイル内容（bytes）
            - "knowledge_type": ナレッジタイプ ("一般的な論文")
            - "mime_type": MIMEタイプ
            - "size": ファイルサイズ
            
        Raises:
            GoogleDriveError: ダウンロードに失敗した場合
        """
        try:
            log_proofreading_info("ナレッジ用PDFファイルダウンロードを開始")
            return self.engine.download_files_from_folder(
                folder_id=folder_id,
                file_type="pdf",
                knowledge_type="一般的な論文"
            )
        except Exception as e:
            raise GoogleDriveError(f"ナレッジ用PDFファイルダウンロードに失敗しました: {e}")
    
    def download_pre_proofread_tex_file(self, folder_id: str) -> bytes:
        """
        校正前のTeXファイルをダウンロード（単一ファイル）
        
        Args:
            folder_id (str): Google DriveフォルダID
            
        Returns:
            bytes: ダウンロードしたファイルの内容
            
        Raises:
            GoogleDriveError: ダウンロードに失敗した場合、またはファイルが見つからない場合
        """
        try:
            log_proofreading_info("校正前TeXファイルダウンロードを開始")
            
            tex_files = self.download_knowledge_tex_files(folder_id)
            
            if not tex_files:
                raise GoogleDriveError(f"フォルダID '{folder_id}' にファイルが見つかりません")
            
            # 最初のファイルを返す（通常は1つのみ）
            first_file = tex_files[0]
            log_proofreading_info(f"校正前ファイル取得完了: {first_file['name']}")
            
            return first_file["content"]
            
        except GoogleDriveError:
            raise
        except Exception as e:
            raise GoogleDriveError(f"校正前TeXファイルダウンロードに失敗しました: {e}")
    
    def download_files_by_type(
        self, 
        folder_id: str, 
        file_type: str,
        knowledge_type: str = None
    ) -> List[Dict[str, Any]]:
        """
        指定されたタイプのファイルをダウンロード
        
        Args:
            folder_id (str): Google DriveフォルダID
            file_type (str): ファイルタイプ ("tex", "pdf", "all")
            knowledge_type (str, optional): カスタムナレッジタイプ
            
        Returns:
            List[Dict[str, Any]]: ダウンロードしたファイルのリスト
            
        Raises:
            GoogleDriveError: ダウンロードに失敗した場合
        """
        try:
            log_proofreading_info(f"指定タイプファイルダウンロードを開始: {file_type}")
            return self.engine.download_files_from_folder(
                folder_id=folder_id,
                file_type=file_type,
                knowledge_type=knowledge_type
            )
        except Exception as e:
            raise GoogleDriveError(f"指定タイプファイルダウンロードに失敗しました: {e}")


# 下位互換性のためのサービスインスタンス
_service = GoogleDriveService()

def download_knowledge_tex_files(folder_id: str) -> List[Dict[str, Any]]:
    """
    下位互換性のための関数ラッパー
    """
    return _service.download_knowledge_tex_files(folder_id)

def download_knowledge_pdf_files(folder_id: str) -> List[Dict[str, Any]]:
    """
    下位互換性のための関数ラッパー
    """
    return _service.download_knowledge_pdf_files(folder_id)

def download_pre_proofread_tex_file(folder_id: str) -> bytes:
    """
    下位互換性のための関数ラッパー
    """
    return _service.download_pre_proofread_tex_file(folder_id)
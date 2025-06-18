"""
Google Drive API操作の核となるエンジン
"""
import io
from typing import List, Dict, Any, Iterator
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError

from app.services.knowledge.utils.google_drive_auth import get_google_drive_service
from app.services.shared.logging_utils import log_proofreading_debug, log_proofreading_info
from app.services.knowledge.config.google_drive_config import (
    DEFAULT_PAGE_SIZE,
    KNOWLEDGE_TYPE_MAPPING,
    FOLDER_QUERY_TEMPLATE,
    PDF_FOLDER_QUERY_TEMPLATE,
    FILES_FIELDS
)
from app.services.shared.exceptions import GoogleDriveError


class GoogleDriveEngine:
    """Google Drive API操作エンジン"""
    
    def __init__(self):
        self.service = None
    
    def get_service(self):
        """Google Drive APIサービスを取得（遅延初期化）"""
        if self.service is None:
            try:
                self.service = get_google_drive_service()
                log_proofreading_debug("Google Drive APIサービスを初期化")
            except Exception as e:
                raise GoogleDriveError(f"Google Drive APIサービスの初期化に失敗しました: {e}")
        return self.service
    
    def list_files_in_folder(self, folder_id: str, query: str = None) -> Iterator[Dict[str, Any]]:
        """
        指定フォルダ内のファイル一覧を取得（ページネーション対応）
        
        Args:
            folder_id (str): フォルダID
            query (str, optional): 追加の検索クエリ
            
        Yields:
            Dict[str, Any]: ファイル情報
            
        Raises:
            GoogleDriveError: ファイル一覧取得に失敗した場合
        """
        try:
            service = self.get_service()
            
            if query:
                search_query = query.format(folder_id=folder_id)
            else:
                search_query = FOLDER_QUERY_TEMPLATE.format(folder_id=folder_id)
            
            log_proofreading_debug(f"Google Driveファイル検索開始: {search_query}")
            
            page_token = None
            total_files = 0
            
            while True:
                response = service.files().list(
                    q=search_query,
                    fields=FILES_FIELDS,
                    pageToken=page_token,
                    pageSize=DEFAULT_PAGE_SIZE,
                ).execute()
                
                files = response.get("files", [])
                total_files += len(files)
                
                for file_info in files:
                    yield file_info
                
                page_token = response.get("nextPageToken")
                if not page_token:
                    break
            
            log_proofreading_info(f"Google Driveファイル検索完了: {total_files}ファイル")
            
        except HttpError as e:
            raise GoogleDriveError(f"Google Driveファイル一覧取得に失敗しました: {e}")
        except Exception as e:
            raise GoogleDriveError(f"予期しないエラーが発生しました: {e}")
    
    def download_file_content(self, file_id: str, file_name: str) -> bytes:
        """
        ファイルコンテンツをダウンロード
        
        Args:
            file_id (str): ファイルID
            file_name (str): ファイル名（ログ用）
            
        Returns:
            bytes: ファイルコンテンツ
            
        Raises:
            GoogleDriveError: ダウンロードに失敗した場合
        """
        try:
            service = self.get_service()
            
            log_proofreading_debug(f"ファイルダウンロード開始: {file_name}")
            
            request = service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    log_proofreading_debug(f"ダウンロード進捗: {int(status.progress() * 100)}%")
            
            fh.seek(0)
            content = fh.read()
            
            log_proofreading_debug(f"ファイルダウンロード完了: {file_name} ({len(content)}bytes)")
            return content
            
        except HttpError as e:
            raise GoogleDriveError(f"ファイル'{file_name}'のダウンロードに失敗しました: {e}")
        except Exception as e:
            raise GoogleDriveError(f"ファイル'{file_name}'のダウンロード中に予期しないエラーが発生しました: {e}")
    
    def create_file_metadata(
        self, 
        file_info: Dict[str, Any], 
        content: bytes, 
        knowledge_type: str
    ) -> Dict[str, Any]:
        """
        ファイルメタデータを作成
        
        Args:
            file_info (Dict[str, Any]): Google Drive APIからのファイル情報
            content (bytes): ファイルコンテンツ
            knowledge_type (str): ナレッジタイプ
            
        Returns:
            Dict[str, Any]: 統一されたファイルメタデータ
        """
        return {
            "id": file_info["id"],
            "name": file_info["name"],
            "mime_type": file_info.get("mimeType", "unknown"),
            "knowledge_type": knowledge_type,
            "content": content,
            "size": len(content)
        }
    
    def download_files_from_folder(
        self, 
        folder_id: str, 
        file_type: str = "all",
        knowledge_type: str = None
    ) -> List[Dict[str, Any]]:
        """
        フォルダからファイル群をダウンロード
        
        Args:
            folder_id (str): フォルダID
            file_type (str): ファイルタイプ ("tex", "pdf", "all")
            knowledge_type (str, optional): 強制的に設定するナレッジタイプ
            
        Returns:
            List[Dict[str, Any]]: ダウンロードしたファイルリスト
            
        Raises:
            GoogleDriveError: ダウンロードに失敗した場合
        """
        try:
            log_proofreading_info(f"フォルダからファイルダウンロード開始: {folder_id} (type: {file_type})")
            
            # クエリの決定
            if file_type == "pdf":
                query = PDF_FOLDER_QUERY_TEMPLATE
                default_knowledge_type = KNOWLEDGE_TYPE_MAPPING.get("pdf")
            else:
                query = FOLDER_QUERY_TEMPLATE
                default_knowledge_type = KNOWLEDGE_TYPE_MAPPING.get("tex")
            
            # ナレッジタイプの決定
            final_knowledge_type = knowledge_type or default_knowledge_type
            
            downloaded_files = []
            for file_info in self.list_files_in_folder(folder_id, query):
                try:
                    content = self.download_file_content(file_info["id"], file_info["name"])
                    file_metadata = self.create_file_metadata(
                        file_info, content, final_knowledge_type
                    )
                    downloaded_files.append(file_metadata)
                    
                except GoogleDriveError as e:
                    log_proofreading_debug(f"ファイル'{file_info['name']}'のダウンロードをスキップ: {e}")
                    continue
            
            log_proofreading_info(f"フォルダダウンロード完了: {len(downloaded_files)}ファイル")
            return downloaded_files
            
        except Exception as e:
            raise GoogleDriveError(f"フォルダ'{folder_id}'からのファイルダウンロードに失敗しました: {e}")
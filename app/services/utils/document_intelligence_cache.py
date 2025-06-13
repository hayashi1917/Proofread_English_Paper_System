import os
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path


class DocumentIntelligenceCache:
    """
    Document Intelligence の処理結果をキャッシュするクラス
    ファイルのハッシュ値をキーとして JSON 形式で保存・取得する
    """
    
    def __init__(self, cache_dir: str = "document_intelligence_cache"):
        """
        キャッシュシステムを初期化
        
        Args:
            cache_dir: キャッシュファイルを保存するディレクトリ
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # メタデータファイルのパス
        self.metadata_file = self.cache_dir / "cache_metadata.json"
        
        # メタデータを初期化または読み込み
        self._load_metadata()
    
    def _load_metadata(self):
        """メタデータファイルを読み込む"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                self.metadata = {}
        else:
            self.metadata = {}
    
    def _save_metadata(self):
        """メタデータファイルを保存する"""
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)
    
    def _get_file_hash(self, file_bytes: bytes) -> str:
        """
        ファイルのSHA256ハッシュ値を計算
        
        Args:
            file_bytes: ファイルのバイトデータ
            
        Returns:
            ハッシュ値（16進数文字列）
        """
        return hashlib.sha256(file_bytes).hexdigest()
    
    def _get_cache_file_path(self, file_hash: str) -> Path:
        """
        キャッシュファイルのパスを取得
        
        Args:
            file_hash: ファイルのハッシュ値
            
        Returns:
            キャッシュファイルのパス
        """
        return self.cache_dir / f"{file_hash}.json"
    
    def has_cache(self, file_bytes: bytes, file_name: str) -> bool:
        """
        指定ファイルのキャッシュが存在するかチェック
        
        Args:
            file_bytes: ファイルのバイトデータ
            file_name: ファイル名
            
        Returns:
            キャッシュが存在する場合True
        """
        file_hash = self._get_file_hash(file_bytes)
        cache_file = self._get_cache_file_path(file_hash)
        
        return cache_file.exists() and file_hash in self.metadata
    
    def get_cache(self, file_bytes: bytes, file_name: str) -> Optional[List[Dict[str, Any]]]:
        """
        キャッシュされた処理結果を取得
        
        Args:
            file_bytes: ファイルのバイトデータ
            file_name: ファイル名
            
        Returns:
            キャッシュされた処理結果、存在しない場合None
        """
        if not self.has_cache(file_bytes, file_name):
            return None
        
        file_hash = self._get_file_hash(file_bytes)
        cache_file = self._get_cache_file_path(file_hash)
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
                
            # メタデータの最終アクセス時刻を更新
            self.metadata[file_hash]["last_accessed"] = datetime.now().isoformat()
            self._save_metadata()
            
            print(f"キャッシュから取得: {file_name} (hash: {file_hash[:8]}...)")
            return cached_data["pages_content"]
            
        except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
            print(f"キャッシュ読み込みエラー: {e}")
            # 破損したキャッシュファイルを削除
            self._remove_cache_file(file_hash)
            return None
    
    def save_cache(self, file_bytes: bytes, file_name: str, pages_content: List[Dict[str, Any]]) -> bool:
        """
        処理結果をキャッシュに保存
        
        Args:
            file_bytes: ファイルのバイトデータ
            file_name: ファイル名
            pages_content: Document Intelligence の処理結果
            
        Returns:
            保存成功時True
        """
        file_hash = self._get_file_hash(file_bytes)
        cache_file = self._get_cache_file_path(file_hash)
        
        try:
            # キャッシュデータを構築
            cache_data = {
                "file_name": file_name,
                "file_hash": file_hash,
                "processed_at": datetime.now().isoformat(),
                "pages_content": pages_content
            }
            
            # キャッシュファイルに保存
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            # メタデータを更新
            self.metadata[file_hash] = {
                "file_name": file_name,
                "cache_file": str(cache_file),
                "created_at": datetime.now().isoformat(),
                "last_accessed": datetime.now().isoformat(),
                "file_size": len(file_bytes),
                "pages_count": len(pages_content)
            }
            self._save_metadata()
            
            print(f"キャッシュに保存: {file_name} (hash: {file_hash[:8]}...)")
            return True
            
        except Exception as e:
            print(f"キャッシュ保存エラー: {e}")
            return False
    
    def _remove_cache_file(self, file_hash: str):
        """キャッシュファイルとメタデータを削除"""
        cache_file = self._get_cache_file_path(file_hash)
        
        if cache_file.exists():
            cache_file.unlink()
        
        if file_hash in self.metadata:
            del self.metadata[file_hash]
            self._save_metadata()
    
    def cleanup_old_cache(self, days: int = 30):
        """
        指定日数より古いキャッシュファイルを削除
        
        Args:
            days: 保持期間（日数）
        """
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        removed_count = 0
        
        for file_hash, metadata in list(self.metadata.items()):
            try:
                created_at = datetime.fromisoformat(metadata["created_at"])
                if created_at < cutoff_date:
                    self._remove_cache_file(file_hash)
                    removed_count += 1
            except (ValueError, KeyError):
                # 不正なメタデータの場合も削除
                self._remove_cache_file(file_hash)
                removed_count += 1
        
        print(f"古いキャッシュファイル {removed_count} 個を削除しました")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        キャッシュの統計情報を取得
        
        Returns:
            キャッシュの統計情報
        """
        total_files = len(self.metadata)
        total_size = sum(metadata.get("file_size", 0) for metadata in self.metadata.values())
        total_pages = sum(metadata.get("pages_count", 0) for metadata in self.metadata.values())
        
        return {
            "total_cached_files": total_files,
            "total_file_size_mb": round(total_size / (1024 * 1024), 2),
            "total_pages_processed": total_pages,
            "cache_directory": str(self.cache_dir),
            "metadata_file": str(self.metadata_file)
        }
    
    def list_cached_files(self) -> List[Dict[str, Any]]:
        """
        キャッシュされたファイルの一覧を取得
        
        Returns:
            キャッシュファイルの情報リスト
        """
        cached_files = []
        
        for file_hash, metadata in self.metadata.items():
            cached_files.append({
                "file_hash": file_hash,
                "file_name": metadata.get("file_name", "Unknown"),
                "created_at": metadata.get("created_at", "Unknown"),
                "last_accessed": metadata.get("last_accessed", "Unknown"),
                "file_size_mb": round(metadata.get("file_size", 0) / (1024 * 1024), 2),
                "pages_count": metadata.get("pages_count", 0)
            })
        
        # 作成日時でソート（新しい順）
        cached_files.sort(key=lambda x: x["created_at"], reverse=True)
        
        return cached_files
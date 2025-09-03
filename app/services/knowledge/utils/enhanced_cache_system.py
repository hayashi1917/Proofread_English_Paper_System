"""
強化されたDocument Intelligence キャッシュシステム

従量課金の最適化のため、PDFファイル全体とページ単位の
両方のレベルでキャッシュを管理する洗練されたシステム。
"""

import os
import json
import hashlib
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum


class CacheLevel(Enum):
    """キャッシュレベル"""
    FULL_DOCUMENT = "full_document"  # PDF全体
    INDIVIDUAL_PAGE = "individual_page"  # 個別ページ


@dataclass
class CacheMetadata:
    """キャッシュメタデータ"""
    file_hash: str
    cache_type: CacheLevel
    original_filename: str
    page_number: Optional[int] = None
    parent_document_hash: Optional[str] = None
    file_size: int = 0
    processing_time: float = 0.0
    created_at: str = ""
    last_accessed: str = ""
    access_count: int = 0
    content_length: int = 0


class EnhancedDocumentIntelligenceCache:
    """
    強化されたDocument Intelligence キャッシュシステム
    
    特徴:
    - 階層キャッシュ（PDF全体 + 個別ページ）
    - SQLiteデータベースによるメタデータ管理
    - コスト最適化機能
    - アクセス統計とレポート
    """
    
    def __init__(self, cache_dir: str = "enhanced_di_cache"):
        """
        強化キャッシュシステムを初期化
        
        Args:
            cache_dir: キャッシュディレクトリ
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # サブディレクトリ作成
        self.full_doc_cache_dir = self.cache_dir / "full_documents"
        self.page_cache_dir = self.cache_dir / "pages"
        self.full_doc_cache_dir.mkdir(exist_ok=True)
        self.page_cache_dir.mkdir(exist_ok=True)
        
        # SQLiteデータベース初期化
        self.db_path = self.cache_dir / "cache_metadata.db"
        self._init_database()
        
        # 統計情報
        self.session_stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "bytes_saved": 0,
            "api_calls_saved": 0
        }
    
    def _init_database(self):
        """SQLiteデータベースを初期化"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS cache_metadata (
                    file_hash TEXT PRIMARY KEY,
                    cache_type TEXT NOT NULL,
                    original_filename TEXT NOT NULL,
                    page_number INTEGER,
                    parent_document_hash TEXT,
                    file_size INTEGER DEFAULT 0,
                    processing_time REAL DEFAULT 0.0,
                    created_at TEXT NOT NULL,
                    last_accessed TEXT NOT NULL,
                    access_count INTEGER DEFAULT 0,
                    content_length INTEGER DEFAULT 0
                )
            ''')
            
            # インデックス作成
            conn.execute('CREATE INDEX IF NOT EXISTS idx_cache_type ON cache_metadata(cache_type)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_parent_hash ON cache_metadata(parent_document_hash)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_filename ON cache_metadata(original_filename)')
            
            conn.commit()
    
    def _get_file_hash(self, file_bytes: bytes, prefix: str = "") -> str:
        """
        ファイルのハッシュ値を計算（プレフィックス付き）
        
        Args:
            file_bytes: ファイルのバイトデータ
            prefix: ハッシュのプレフィックス（ページ番号など）
            
        Returns:
            ハッシュ値
        """
        hasher = hashlib.sha256()
        if prefix:
            hasher.update(prefix.encode('utf-8'))
        hasher.update(file_bytes)
        return hasher.hexdigest()
    
    def _get_cache_file_path(self, file_hash: str, cache_level: CacheLevel) -> Path:
        """キャッシュファイルのパスを取得"""
        if cache_level == CacheLevel.FULL_DOCUMENT:
            return self.full_doc_cache_dir / f"{file_hash}.json"
        else:
            return self.page_cache_dir / f"{file_hash}.json"
    
    def _save_cache_metadata(self, metadata: CacheMetadata):
        """メタデータをデータベースに保存"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO cache_metadata 
                (file_hash, cache_type, original_filename, page_number, parent_document_hash,
                 file_size, processing_time, created_at, last_accessed, access_count, content_length)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                metadata.file_hash,
                metadata.cache_type.value,
                metadata.original_filename,
                metadata.page_number,
                metadata.parent_document_hash,
                metadata.file_size,
                metadata.processing_time,
                metadata.created_at,
                metadata.last_accessed,
                metadata.access_count,
                metadata.content_length
            ))
            conn.commit()
    
    def _get_cache_metadata(self, file_hash: str) -> Optional[CacheMetadata]:
        """メタデータをデータベースから取得"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                'SELECT * FROM cache_metadata WHERE file_hash = ?',
                (file_hash,)
            )
            row = cursor.fetchone()
            
            if row:
                return CacheMetadata(
                    file_hash=row[0],
                    cache_type=CacheLevel(row[1]),
                    original_filename=row[2],
                    page_number=row[3],
                    parent_document_hash=row[4],
                    file_size=row[5],
                    processing_time=row[6],
                    created_at=row[7],
                    last_accessed=row[8],
                    access_count=row[9],
                    content_length=row[10]
                )
        return None
    
    def _update_access_info(self, file_hash: str):
        """アクセス情報を更新"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                UPDATE cache_metadata 
                SET last_accessed = ?, access_count = access_count + 1
                WHERE file_hash = ?
            ''', (datetime.now().isoformat(), file_hash))
            conn.commit()
    
    def has_full_document_cache(self, file_bytes: bytes, filename: str) -> bool:
        """PDF全体のキャッシュが存在するかチェック"""
        file_hash = self._get_file_hash(file_bytes)
        cache_file = self._get_cache_file_path(file_hash, CacheLevel.FULL_DOCUMENT)
        metadata = self._get_cache_metadata(file_hash)
        
        return cache_file.exists() and metadata is not None
    
    def has_page_cache(self, page_bytes: bytes, filename: str, page_number: int, parent_hash: str) -> bool:
        """個別ページのキャッシュが存在するかチェック"""
        page_hash = self._get_file_hash(page_bytes, f"page_{page_number}")
        cache_file = self._get_cache_file_path(page_hash, CacheLevel.INDIVIDUAL_PAGE)
        metadata = self._get_cache_metadata(page_hash)
        
        return cache_file.exists() and metadata is not None
    
    def get_full_document_cache(self, file_bytes: bytes, filename: str) -> Optional[List[Dict[str, Any]]]:
        """PDF全体のキャッシュを取得"""
        file_hash = self._get_file_hash(file_bytes)
        
        if not self.has_full_document_cache(file_bytes, filename):
            self.session_stats["cache_misses"] += 1
            return None
        
        try:
            cache_file = self._get_cache_file_path(file_hash, CacheLevel.FULL_DOCUMENT)
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
            
            # アクセス情報更新
            self._update_access_info(file_hash)
            self.session_stats["cache_hits"] += 1
            self.session_stats["api_calls_saved"] += 1
            
            print(f"📋 全文書キャッシュヒット: {filename}")
            return cached_data["pages_content"]
            
        except Exception as e:
            print(f"❌ 全文書キャッシュ読み込みエラー: {e}")
            self.session_stats["cache_misses"] += 1
            return None
    
    def get_page_cache(self, page_bytes: bytes, filename: str, page_number: int, parent_hash: str) -> Optional[Dict[str, Any]]:
        """個別ページのキャッシュを取得"""
        page_hash = self._get_file_hash(page_bytes, f"page_{page_number}")
        
        if not self.has_page_cache(page_bytes, filename, page_number, parent_hash):
            self.session_stats["cache_misses"] += 1
            return None
        
        try:
            cache_file = self._get_cache_file_path(page_hash, CacheLevel.INDIVIDUAL_PAGE)
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
            
            # アクセス情報更新
            self._update_access_info(page_hash)
            self.session_stats["cache_hits"] += 1
            self.session_stats["api_calls_saved"] += 1
            
            print(f"📄 ページキャッシュヒット: {filename} ページ{page_number}")
            return cached_data["page_content"]
            
        except Exception as e:
            print(f"❌ ページキャッシュ読み込みエラー: {e}")
            self.session_stats["cache_misses"] += 1
            return None
    
    def save_full_document_cache(self, file_bytes: bytes, filename: str, pages_content: List[Dict[str, Any]], processing_time: float = 0.0) -> bool:
        """PDF全体のキャッシュを保存"""
        file_hash = self._get_file_hash(file_bytes)
        
        try:
            # キャッシュデータ構築
            cache_data = {
                "file_hash": file_hash,
                "filename": filename,
                "cached_at": datetime.now().isoformat(),
                "cache_type": "full_document",
                "pages_content": pages_content
            }
            
            # ファイル保存
            cache_file = self._get_cache_file_path(file_hash, CacheLevel.FULL_DOCUMENT)
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            # メタデータ保存
            metadata = CacheMetadata(
                file_hash=file_hash,
                cache_type=CacheLevel.FULL_DOCUMENT,
                original_filename=filename,
                file_size=len(file_bytes),
                processing_time=processing_time,
                created_at=datetime.now().isoformat(),
                last_accessed=datetime.now().isoformat(),
                access_count=0,
                content_length=len(json.dumps(pages_content))
            )
            self._save_cache_metadata(metadata)
            
            print(f"💾 全文書キャッシュ保存: {filename}")
            return True
            
        except Exception as e:
            print(f"❌ 全文書キャッシュ保存エラー: {e}")
            return False
    
    def save_page_cache(self, page_bytes: bytes, filename: str, page_number: int, parent_hash: str, page_content: Dict[str, Any], processing_time: float = 0.0) -> bool:
        """個別ページのキャッシュを保存"""
        page_hash = self._get_file_hash(page_bytes, f"page_{page_number}")
        
        try:
            # キャッシュデータ構築
            cache_data = {
                "page_hash": page_hash,
                "filename": filename,
                "page_number": page_number,
                "parent_document_hash": parent_hash,
                "cached_at": datetime.now().isoformat(),
                "cache_type": "individual_page",
                "page_content": page_content
            }
            
            # ファイル保存
            cache_file = self._get_cache_file_path(page_hash, CacheLevel.INDIVIDUAL_PAGE)
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            # メタデータ保存
            metadata = CacheMetadata(
                file_hash=page_hash,
                cache_type=CacheLevel.INDIVIDUAL_PAGE,
                original_filename=filename,
                page_number=page_number,
                parent_document_hash=parent_hash,
                file_size=len(page_bytes),
                processing_time=processing_time,
                created_at=datetime.now().isoformat(),
                last_accessed=datetime.now().isoformat(),
                access_count=0,
                content_length=len(json.dumps(page_content))
            )
            self._save_cache_metadata(metadata)
            
            print(f"💾 ページキャッシュ保存: {filename} ページ{page_number}")
            return True
            
        except Exception as e:
            print(f"❌ ページキャッシュ保存エラー: {e}")
            return False
    
    def get_cache_recommendations(self) -> Dict[str, Any]:
        """キャッシュ最適化の推奨事項を生成"""
        with sqlite3.connect(self.db_path) as conn:
            # 全体統計
            total_count = conn.execute('SELECT COUNT(*) FROM cache_metadata').fetchone()[0]
            
            # アクセス頻度分析
            low_access = conn.execute(
                'SELECT COUNT(*) FROM cache_metadata WHERE access_count <= 1'
            ).fetchone()[0]
            
            # サイズ分析
            large_files = conn.execute(
                'SELECT COUNT(*) FROM cache_metadata WHERE file_size > 5242880'  # 5MB
            ).fetchone()[0]
            
            # 古いファイル
            cutoff_date = (datetime.now() - timedelta(days=30)).isoformat()
            old_files = conn.execute(
                'SELECT COUNT(*) FROM cache_metadata WHERE last_accessed < ?',
                (cutoff_date,)
            ).fetchone()[0]
        
        recommendations = []
        
        if low_access > total_count * 0.3:
            recommendations.append("低アクセスファイルが多いです。定期的なクリーンアップを推奨します。")
        
        if large_files > 0:
            recommendations.append(f"{large_files}個の大きなファイルがキャッシュされています。")
        
        if old_files > 0:
            recommendations.append(f"{old_files}個の古いキャッシュファイルの削除を検討してください。")
        
        return {
            "total_cached_items": total_count,
            "low_access_items": low_access,
            "large_files": large_files,
            "old_files": old_files,
            "recommendations": recommendations,
            "session_stats": self.session_stats
        }
    
    def cleanup_by_criteria(self, days_old: int = 30, min_access_count: int = 1, max_size_mb: float = None) -> int:
        """条件に基づくキャッシュクリーンアップ"""
        removed_count = 0
        cutoff_date = (datetime.now() - timedelta(days=days_old)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            # 削除対象を特定
            query = '''
                SELECT file_hash, cache_type FROM cache_metadata 
                WHERE (last_accessed < ? OR access_count < ?)
            '''
            params = [cutoff_date, min_access_count]
            
            if max_size_mb:
                query += ' OR file_size > ?'
                params.append(max_size_mb * 1024 * 1024)
            
            cursor = conn.execute(query, params)
            items_to_remove = cursor.fetchall()
            
            for file_hash, cache_type in items_to_remove:
                try:
                    # ファイル削除
                    cache_level = CacheLevel(cache_type)
                    cache_file = self._get_cache_file_path(file_hash, cache_level)
                    if cache_file.exists():
                        cache_file.unlink()
                    
                    # メタデータ削除
                    conn.execute('DELETE FROM cache_metadata WHERE file_hash = ?', (file_hash,))
                    removed_count += 1
                    
                except Exception as e:
                    print(f"キャッシュアイテム削除エラー {file_hash}: {e}")
            
            conn.commit()
        
        print(f"🧹 {removed_count}個のキャッシュアイテムを削除しました")
        return removed_count
    
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """包括的な統計情報を取得"""
        with sqlite3.connect(self.db_path) as conn:
            # 基本統計
            stats = {}
            
            # タイプ別統計
            cursor = conn.execute('''
                SELECT cache_type, COUNT(*), SUM(file_size), AVG(processing_time), SUM(access_count)
                FROM cache_metadata GROUP BY cache_type
            ''')
            
            for cache_type, count, total_size, avg_time, total_access in cursor:
                stats[cache_type] = {
                    "count": count,
                    "total_size_mb": round((total_size or 0) / (1024 * 1024), 2),
                    "avg_processing_time": round(avg_time or 0, 2),
                    "total_accesses": total_access or 0
                }
            
            # 全体統計
            cursor = conn.execute('''
                SELECT COUNT(*), SUM(file_size), AVG(processing_time), SUM(access_count)
                FROM cache_metadata
            ''')
            total_count, total_size, avg_time, total_access = cursor.fetchone()
            
            stats["overall"] = {
                "total_items": total_count or 0,
                "total_size_mb": round((total_size or 0) / (1024 * 1024), 2),
                "avg_processing_time": round(avg_time or 0, 2),
                "total_accesses": total_access or 0,
                "cache_directory": str(self.cache_dir)
            }
            
            # セッション統計追加
            stats["session"] = self.session_stats
            
        return stats
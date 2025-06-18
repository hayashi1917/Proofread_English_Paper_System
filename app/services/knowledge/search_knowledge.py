"""
知識ベース検索サービス

ベクターストアから学術論文校正に関する知識を検索し、
各種フィルタリング条件に基づいた柔軟な検索機能を提供します。
"""
from typing import List, Any, Optional

from app.services.shared.client_factory import ClientFactory
from app.services.shared.logging_utils import log_proofreading_info, log_proofreading_debug
from app.services.knowledge.config.knowledge_search_config import (
    DEFAULT_SEARCH_LIMIT,
    MIN_QUERY_LENGTH,
    MAX_QUERY_LENGTH,
    SearchType
)
from app.services.shared.exceptions import VectorStoreError


class KnowledgeSearchService:
    """知識ベース検索サービス"""
    
    def __init__(self):
        self.vector_store = None
    
    def get_vector_store(self):
        """ベクターストアを取得（遅延初期化）"""
        if self.vector_store is None:
            try:
                self.vector_store = ClientFactory.get_vector_store()
                log_proofreading_debug("ベクターストアを初期化")
            except Exception as e:
                raise VectorStoreError(f"ベクターストアの初期化に失敗しました: {e}")
        return self.vector_store
    
    def validate_query(self, query: str) -> None:
        """
        検索クエリの妥当性を検証
        
        Args:
            query (str): 検索クエリ
            
        Raises:
            VectorStoreError: クエリが無効な場合
        """
        if not query or not query.strip():
            raise VectorStoreError("検索クエリが空です")
        
        query_length = len(query.strip())
        if query_length < MIN_QUERY_LENGTH:
            raise VectorStoreError(f"検索クエリが短すぎます (最小: {MIN_QUERY_LENGTH}文字)")
        
        if query_length > MAX_QUERY_LENGTH:
            raise VectorStoreError(f"検索クエリが長すぎます (最大: {MAX_QUERY_LENGTH}文字)")
    
    def search_knowledge_from_vector_store(
        self, 
        query: str, 
        limit: int = DEFAULT_SEARCH_LIMIT
    ) -> List[Any]:
        """
        一般的な知識検索
        
        Args:
            query (str): 検索クエリ
            limit (int): 検索結果の最大数
            
        Returns:
            List[Any]: 検索された知識のリスト
            
        Raises:
            VectorStoreError: 検索処理に失敗した場合
        """
        try:
            self.validate_query(query)
            
            log_proofreading_info(f"一般知識検索を開始: '{query}'")
            log_proofreading_debug("検索パラメータ", {"query": query, "limit": limit})
            
            vector_store = self.get_vector_store()
            knowledge_list = vector_store.get_knowledge_from_vector_store(query, k=limit)
            
            log_proofreading_info(f"一般知識検索完了: {len(knowledge_list)}件")
            return knowledge_list
            
        except Exception as e:
            raise VectorStoreError(f"一般知識検索中にエラーが発生しました: {e}")
    
    def search_knowledge_from_vector_store_by_issue_category(
        self, 
        query: str, 
        issue_category: str,
        limit: int = DEFAULT_SEARCH_LIMIT
    ) -> List[Any]:
        """
        問題カテゴリでフィルタした知識検索
        
        Args:
            query (str): 検索クエリ
            issue_category (str): 問題カテゴリ
            limit (int): 検索結果の最大数
            
        Returns:
            List[Any]: 検索された知識のリスト
            
        Raises:
            VectorStoreError: 検索処理に失敗した場合
        """
        try:
            self.validate_query(query)
            
            if not issue_category or not issue_category.strip():
                raise VectorStoreError("問題カテゴリが指定されていません")
            
            log_proofreading_info(f"カテゴリ別知識検索を開始: '{query}' (カテゴリ: {issue_category})")
            log_proofreading_debug("検索パラメータ", {
                "query": query, 
                "issue_category": issue_category, 
                "limit": limit
            })
            
            vector_store = self.get_vector_store()
            knowledge_list = vector_store.get_knowledge_from_vector_store_by_issue_category(
                query, issue_category
            )
            
            log_proofreading_info(f"カテゴリ別知識検索完了: {len(knowledge_list)}件")
            return knowledge_list
            
        except Exception as e:
            raise VectorStoreError(f"カテゴリ別知識検索中にエラーが発生しました: {e}")
    
    def search_knowledge_from_vector_store_by_knowledge_type(
        self, 
        query: str, 
        knowledge_type: str,
        limit: int = DEFAULT_SEARCH_LIMIT
    ) -> List[Any]:
        """
        知識タイプでフィルタした知識検索
        
        Args:
            query (str): 検索クエリ
            knowledge_type (str): 知識タイプ
            limit (int): 検索結果の最大数
            
        Returns:
            List[Any]: 検索された知識のリスト
            
        Raises:
            VectorStoreError: 検索処理に失敗した場合
        """
        try:
            self.validate_query(query)
            
            if not knowledge_type or not knowledge_type.strip():
                raise VectorStoreError("知識タイプが指定されていません")
            
            log_proofreading_info(f"タイプ別知識検索を開始: '{query}' (タイプ: {knowledge_type})")
            log_proofreading_debug("検索パラメータ", {
                "query": query, 
                "knowledge_type": knowledge_type, 
                "limit": limit
            })
            
            vector_store = self.get_vector_store()
            knowledge_list = vector_store.get_knowledge_from_vector_store_by_knowledge_type(
                query, knowledge_type
            )
            
            log_proofreading_info(f"タイプ別知識検索完了: {len(knowledge_list)}件")
            return knowledge_list
            
        except Exception as e:
            raise VectorStoreError(f"タイプ別知識検索中にエラーが発生しました: {e}")
    
    def delete_all_knowledge_from_vector_store(self) -> bool:
        """
        ベクターストアから全ての知識を削除
        
        Returns:
            bool: 削除が成功した場合True
            
        Raises:
            VectorStoreError: 削除処理に失敗した場合
        """
        try:
            log_proofreading_info("全知識削除を開始")
            
            vector_store = self.get_vector_store()
            result = vector_store.delete_all_knowledge_from_vector_store()
            
            if result:
                log_proofreading_info("全知識削除が完了")
            else:
                log_proofreading_info("全知識削除が失敗")
                
            return result
            
        except Exception as e:
            raise VectorStoreError(f"全知識削除中にエラーが発生しました: {e}")
    
    def search_knowledge_with_options(
        self,
        query: str,
        search_type: str = SearchType.GENERAL,
        filter_value: Optional[str] = None,
        limit: int = DEFAULT_SEARCH_LIMIT
    ) -> List[Any]:
        """
        オプション指定による柔軟な知識検索
        
        Args:
            query (str): 検索クエリ
            search_type (str): 検索タイプ
            filter_value (str, optional): フィルタ値（カテゴリまたはタイプ）
            limit (int): 検索結果の最大数
            
        Returns:
            List[Any]: 検索された知識のリスト
            
        Raises:
            VectorStoreError: 検索処理に失敗した場合
        """
        try:
            if search_type == SearchType.GENERAL:
                return self.search_knowledge_from_vector_store(query, limit)
            elif search_type == SearchType.BY_ISSUE_CATEGORY:
                if not filter_value:
                    raise VectorStoreError("カテゴリ検索にはfilter_valueが必要です")
                return self.search_knowledge_from_vector_store_by_issue_category(
                    query, filter_value, limit
                )
            elif search_type == SearchType.BY_KNOWLEDGE_TYPE:
                if not filter_value:
                    raise VectorStoreError("タイプ検索にはfilter_valueが必要です")
                return self.search_knowledge_from_vector_store_by_knowledge_type(
                    query, filter_value, limit
                )
            else:
                raise VectorStoreError(f"サポートされていない検索タイプです: {search_type}")
                
        except Exception as e:
            raise VectorStoreError(f"オプション指定検索中にエラーが発生しました: {e}")


# 下位互換性のためのサービスインスタンス
_service = KnowledgeSearchService()

def search_knowledge_from_vector_store(query: str) -> List[Any]:
    """
    下位互換性のための関数ラッパー
    """
    return _service.search_knowledge_from_vector_store(query)

def search_knowledge_from_vector_store_by_issue_category(query: str, issue_category: str) -> List[Any]:
    """
    下位互換性のための関数ラッパー
    """
    return _service.search_knowledge_from_vector_store_by_issue_category(query, issue_category)

def search_knowledge_from_vector_store_by_knowledge_type(query: str, knowledge_type: str) -> List[Any]:
    """
    下位互換性のための関数ラッパー
    """
    return _service.search_knowledge_from_vector_store_by_knowledge_type(query, knowledge_type)

def delete_all_knowledge_from_vector_store() -> bool:
    """
    下位互換性のための関数ラッパー
    """
    return _service.delete_all_knowledge_from_vector_store()
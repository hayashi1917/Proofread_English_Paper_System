"""
HyDE (Hypothetical Document Embeddings) 手法によるクエリ生成サービス

英語学術論文の校正に必要な検索クエリを、仮想的な文書埋め込み手法により生成します。
"""
from typing import List, Dict, Any

from app.services.proofreading.core.hyde_engine import HyDEEngine
from app.services.shared.logging_utils import log_proofreading_info
from app.services.shared.exceptions import ProofreadingError


class HyDEService:
    """HyDE手法によるクエリ生成サービス"""
    
    def __init__(self):
        self.engine = HyDEEngine()
    
    def create_queries_by_HyDE(self, section: str) -> List[str]:
        """
        HyDE手法を使用した英語論文校正クエリ生成
        
        与えられたLaTeXセクションを分析し、潜在的な文法・語法・表現・構造上の
        問題を特定し、その問題解決に必要な校正知識を検索するための
        具体的なクエリを生成します。

        HyDEプロセス:
        1. セクション内容の言語学的分析
        2. 潜在的文法・語法問題の仮定
        3. 問題解決に必要な理想的校正知識の想定
        4. 知識ベース検索用クエリの具体化

        Args:
            section (str): 校正対象のLaTeXセクションテキスト

        Returns:
            List[str]: 英語論文校正用の具体的検索クエリリスト
                      （文法項目、表現技法、専門用語、構造上の改善点等）
                      
        Raises:
            ProofreadingError: クエリ生成に失敗した場合
        """
        try:
            log_proofreading_info("単一セクションのHyDEクエリ生成を開始")
            return self.engine.generate_queries(section)
        except Exception as e:
            raise ProofreadingError(f"HyDEクエリ生成中にエラーが発生しました: {e}")
    
    def create_queries_by_HyDE_from_sections(self, sections: List[str]) -> List[List[str]]:
        """
        複数セクションからHyDEクエリを生成
        
        Args:
            sections (List[str]): セクションのリスト
            
        Returns:
            List[List[str]]: 各セクションに対応するクエリリストのリスト
            
        Raises:
            ProofreadingError: クエリ生成に失敗した場合
        """
        try:
            log_proofreading_info("複数セクションのHyDEクエリ生成を開始")
            return self.engine.generate_queries_from_sections(sections)
        except Exception as e:
            raise ProofreadingError(f"複数セクションHyDEクエリ生成中にエラーが発生しました: {e}")


# 下位互換性のためのサービスインスタンス
_service = HyDEService()

def create_queries_by_HyDE(section: str) -> List[str]:
    """
    下位互換性のための関数ラッパー
    
    Args:
        section (str): 校正対象のLaTeXセクションテキスト
        
    Returns:
        List[str]: 生成されたクエリリスト
    """
    return _service.create_queries_by_HyDE(section)

def create_queries_by_HyDE_from_sections(sections: List[str]) -> List[List[str]]:
    """
    下位互換性のための関数ラッパー
    
    Args:
        sections (List[str]): セクションのリスト
        
    Returns:
        List[List[str]]: 各セクションに対応するクエリリストのリスト
    """
    return _service.create_queries_by_HyDE_from_sections(sections)
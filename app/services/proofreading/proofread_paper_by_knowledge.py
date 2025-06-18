"""
論文校正サービス

知識ベースを活用した英語学術論文の校正処理を提供します。
"""
from typing import List, Dict, Any, Tuple

from app.schemas.schemas import ProofreadResult
from app.services.proofreading.create_queries_by_HyDE import create_queries_by_HyDE
from app.services.proofreading.core.proofreading_engine import ProofreadingEngine
from app.services.shared.logging_utils import log_proofreading_info, log_proofreading_debug
from app.services.proofreading.utils.proofreading_utils import (
    create_proofread_section_dict,
    create_proofread_section_dict_without_knowledge
)
from app.services.shared.exceptions import ProofreadingError


class ProofreadingService:
    """論文校正サービスクラス"""
    
    def __init__(self):
        self.engine = ProofreadingEngine()
    
    def proofread_section_by_knowledge(
        self, 
        section_text: str, 
        queries: List[str]
    ) -> Tuple[ProofreadResult, str]:
        """
        英文セクションを知識ベースの情報で校正し、結果を返す
        
        Args:
            section_text (str): 校正対象 LaTeX セクション全体の文字列
            queries (List[str]): ベクターストア検索に使うクエリ語句
        
        Returns:
            Tuple[ProofreadResult, str]: 校正結果と使用した知識
        """
        try:
            log_proofreading_info("知識ベース校正を開始")
            return self.engine.proofread_section_with_knowledge(section_text, queries)
        except Exception as e:
            raise ProofreadingError(f"知識ベース校正中にエラーが発生しました: {e}")
    
    def proofread_section_without_knowledge(self, section_text: str) -> ProofreadResult:
        """
        論文のセクションを校正する（ナレッジベースを使用しない）
        
        Args:
            section_text (str): 校正対象テキスト
            
        Returns:
            ProofreadResult: 校正結果
        """
        try:
            log_proofreading_info("単独校正を開始")
            return self.engine.execute_proofreading_without_knowledge(section_text)
        except Exception as e:
            raise ProofreadingError(f"単独校正中にエラーが発生しました: {e}")
    
    def proofread_paper_by_knowledge(self, sections: List[str]) -> List[Dict[str, Any]]:
        """
        論文全体を知識ベースからの情報を用いて校正する
        
        Args:
            sections (List[str]): 論文のセクションリスト
        
        Returns:
            List[Dict[str, Any]]: 校正結果を含む論文のセクションリスト
        """
        log_proofreading_info(f"論文全体校正を開始 ({len(sections)}セクション)")
        proofread_sections = []
        
        for i, section in enumerate(sections):
            log_proofreading_debug(f"セクション {i+1}/{len(sections)} を処理中")
            
            queries = create_queries_by_HyDE(section)
            log_proofreading_debug("生成されたクエリ", queries)
            
            proofread_result, knowledge = self.proofread_section_by_knowledge(section, queries)
            
            section_dict = create_proofread_section_dict(proofread_result, queries, knowledge)
            proofread_sections.append(section_dict)
        
        log_proofreading_info("論文全体校正が完了")
        return proofread_sections
    
    def proofread_paper_without_knowledge(self, sections: List[str]) -> List[Dict[str, Any]]:
        """
        論文全体を知識ベースからの情報を用いずに校正する
        
        Args:
            sections (List[str]): 論文のセクションリスト
        
        Returns:
            List[Dict[str, Any]]: 校正結果を含む論文のセクションリスト
        """
        log_proofreading_info(f"論文全体校正を開始 (知識ベースなし, {len(sections)}セクション)")
        proofread_sections = []
        
        for i, section in enumerate(sections):
            log_proofreading_debug(f"セクション {i+1}/{len(sections)} を処理中")
            
            proofread_result = self.proofread_section_without_knowledge(section)
            section_dict = create_proofread_section_dict_without_knowledge(proofread_result)
            proofread_sections.append(section_dict)
        
        log_proofreading_info("論文全体校正が完了 (知識ベースなし)")
        return proofread_sections


# 下位互換性のための関数ラッパー
_service = ProofreadingService()

def proofread_section_by_knowledge(
    section_text: str, 
    queries: List[str]
) -> Tuple[ProofreadResult, str]:
    """
    下位互換性のための関数ラッパー
    """
    return _service.proofread_section_by_knowledge(section_text, queries)

def proofread_paper_by_knowledge(sections: List[str]) -> List[Dict[str, Any]]:
    """
    下位互換性のための関数ラッパー
    """
    return _service.proofread_paper_by_knowledge(sections)

def proofread_section_without_knowledge(section: str) -> ProofreadResult:
    """
    下位互換性のための関数ラッパー
    """
    return _service.proofread_section_without_knowledge(section)

def proofread_paper_without_knowledge(sections: List[str]) -> List[Dict[str, Any]]:
    """
    下位互換性のための関数ラッパー
    """
    return _service.proofread_paper_without_knowledge(sections)
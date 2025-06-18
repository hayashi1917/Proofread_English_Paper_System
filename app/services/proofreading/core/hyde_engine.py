"""
HyDE (Hypothetical Document Embeddings) クエリ生成エンジン
"""
from typing import List
from langchain.prompts import ChatPromptTemplate

from app.schemas.schemas import CreateQueriesByHyDE
from app.services.shared.client_factory import ClientFactory
from app.services.shared.logging_utils import log_proofreading_debug, log_proofreading_info
from app.services.proofreading.prompts.hyde_prompts import HYDE_SYSTEM_PROMPT, HYDE_USER_PROMPT
from app.services.proofreading.config.hyde_config import (
    SECTION_MIN_LENGTH, 
    SECTION_MAX_LENGTH,
    HYDE_DEFAULT_MAX_QUERIES,
    HYDE_DEFAULT_MIN_QUERIES
)
from app.services.shared.exceptions import ProofreadingError


class HyDEEngine:
    """HyDE手法によるクエリ生成エンジン"""
    
    def __init__(self):
        self.openai_client = ClientFactory.get_openai_client()
    
    def validate_section(self, section: str) -> None:
        """
        セクションの妥当性を検証
        
        Args:
            section (str): 検証対象のセクション
            
        Raises:
            ProofreadingError: セクションが無効な場合
        """
        if not section or not section.strip():
            raise ProofreadingError("セクションが空です")
        
        section_length = len(section.strip())
        if section_length < SECTION_MIN_LENGTH:
            raise ProofreadingError(f"セクションが短すぎます (最小: {SECTION_MIN_LENGTH}文字)")
        
        if section_length > SECTION_MAX_LENGTH:
            raise ProofreadingError(f"セクションが長すぎます (最大: {SECTION_MAX_LENGTH}文字)")
    
    def generate_queries(self, section: str) -> List[str]:
        """
        HyDE手法を使用してセクションから校正クエリを生成
        
        Args:
            section (str): 分析対象のLaTeXセクション
            
        Returns:
            List[str]: 生成された検索クエリのリスト
            
        Raises:
            ProofreadingError: クエリ生成に失敗した場合
        """
        try:
            self.validate_section(section)
            
            log_proofreading_debug("HyDEクエリ生成開始", {
                "section_length": len(section),
                "section_preview": section[:100] + "..." if len(section) > 100 else section
            })
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", HYDE_SYSTEM_PROMPT),
                ("user", HYDE_USER_PROMPT),
            ])
            
            chain = prompt | self.openai_client.get_openai_client().with_structured_output(CreateQueriesByHyDE)
            result = chain.invoke({"section_content": section})
            
            queries = result.queries if result.queries else []
            
            # クエリ数の検証
            if len(queries) < HYDE_DEFAULT_MIN_QUERIES:
                log_proofreading_debug(f"生成されたクエリ数が少ないです: {len(queries)}")
            elif len(queries) > HYDE_DEFAULT_MAX_QUERIES:
                log_proofreading_debug(f"生成されたクエリ数が多いため、上位{HYDE_DEFAULT_MAX_QUERIES}個に制限")
                queries = queries[:HYDE_DEFAULT_MAX_QUERIES]
            
            log_proofreading_info(f"HyDEクエリ生成完了: {len(queries)}個のクエリを生成")
            log_proofreading_debug("生成されたクエリ", queries)
            
            return queries
            
        except Exception as e:
            raise ProofreadingError(f"HyDEクエリ生成中にエラーが発生しました: {e}")
    
    def generate_queries_from_sections(self, sections: List[str]) -> List[List[str]]:
        """
        複数のセクションからクエリを生成
        
        Args:
            sections (List[str]): セクションのリスト
            
        Returns:
            List[List[str]]: 各セクションに対応するクエリリストのリスト
        """
        log_proofreading_info(f"複数セクションのHyDEクエリ生成開始: {len(sections)}セクション")
        
        all_queries = []
        for i, section in enumerate(sections):
            log_proofreading_debug(f"セクション {i+1}/{len(sections)} を処理中")
            queries = self.generate_queries(section)
            all_queries.append(queries)
        
        log_proofreading_info("複数セクションのHyDEクエリ生成完了")
        return all_queries
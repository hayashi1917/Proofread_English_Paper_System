"""
LaTeXテキストからの知識抽出エンジン
"""
from typing import List, Dict, Any
from langchain_core.prompts import ChatPromptTemplate

from app.schemas.schemas import KnowledgeFromLatexList, KnowledgeFromLatex
from app.services.shared.client_factory import ClientFactory
from app.services.shared.logging_utils import log_proofreading_debug, log_proofreading_info
from app.services.knowledge.prompts.knowledge_extraction_prompts import (
    KNOWLEDGE_EXTRACTION_SYSTEM_PROMPT,
    KNOWLEDGE_EXTRACTION_USER_PROMPT
)
from app.services.knowledge.config.knowledge_extraction_config import (
    MIN_KNOWLEDGE_DESCRIPTION_LENGTH,
    MAX_KNOWLEDGE_DESCRIPTION_LENGTH,
    EXCLUDE_EMPTY_KNOWLEDGE,
    EXCLUDE_DUPLICATE_KNOWLEDGE
)
from app.services.shared.exceptions import KnowledgeExtractionError


class KnowledgeExtractionEngine:
    """LaTeXテキストからの知識抽出エンジン"""
    
    def __init__(self):
        self.openai_client = ClientFactory.get_openai_client()
    
    def validate_knowledge_item(self, knowledge: KnowledgeFromLatex) -> bool:
        """
        抽出された知識項目の妥当性を検証
        
        Args:
            knowledge (KnowledgeFromLatex): 検証対象の知識項目
            
        Returns:
            bool: 妥当な場合True
        """
        if not knowledge.description or not knowledge.description.strip():
            log_proofreading_debug("空の知識項目をスキップ")
            return False
        
        description_length = len(knowledge.description.strip())
        if description_length < MIN_KNOWLEDGE_DESCRIPTION_LENGTH:
            log_proofreading_debug(f"短すぎる知識項目をスキップ: {knowledge.description[:50]}")
            return False
        
        if description_length > MAX_KNOWLEDGE_DESCRIPTION_LENGTH:
            log_proofreading_debug(f"長すぎる知識項目をスキップ: {knowledge.description[:50]}...")
            return False
        
        return True
    
    def filter_duplicate_knowledge(self, knowledge_list: List[KnowledgeFromLatex]) -> List[KnowledgeFromLatex]:
        """
        重複する知識項目を除去
        
        Args:
            knowledge_list (List[KnowledgeFromLatex]): 知識項目リスト
            
        Returns:
            List[KnowledgeFromLatex]: 重複除去済み知識項目リスト
        """
        if not EXCLUDE_DUPLICATE_KNOWLEDGE:
            return knowledge_list
        
        seen_descriptions = set()
        filtered_knowledge = []
        
        for knowledge in knowledge_list:
            description_key = knowledge.description.strip().lower()
            if description_key not in seen_descriptions:
                seen_descriptions.add(description_key)
                filtered_knowledge.append(knowledge)
            else:
                log_proofreading_debug(f"重複知識項目をスキップ: {knowledge.description[:50]}")
        
        if len(filtered_knowledge) != len(knowledge_list):
            log_proofreading_debug(f"重複除去: {len(knowledge_list)} → {len(filtered_knowledge)}")
        
        return filtered_knowledge
    
    def process_chunk_to_knowledge(
        self, 
        chunk_text: str, 
        document_name: str, 
        knowledge_type: str
    ) -> List[KnowledgeFromLatex]:
        """
        単一チャンクから知識を抽出
        
        Args:
            chunk_text (str): 処理対象のチャンクテキスト
            document_name (str): ドキュメント名
            knowledge_type (str): ナレッジタイプ
            
        Returns:
            List[KnowledgeFromLatex]: 抽出された知識項目リスト
            
        Raises:
            KnowledgeExtractionError: 知識抽出に失敗した場合
        """
        try:
            log_proofreading_debug("チャンクからの知識抽出開始", {
                "document_name": document_name,
                "knowledge_type": knowledge_type,
                "chunk_length": len(chunk_text),
                "chunk_preview": chunk_text[:100] + "..." if len(chunk_text) > 100 else chunk_text
            })
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", KNOWLEDGE_EXTRACTION_SYSTEM_PROMPT),
                ("user", KNOWLEDGE_EXTRACTION_USER_PROMPT),
            ])
            
            chain = prompt | self.openai_client.get_openai_client().with_structured_output(KnowledgeFromLatexList)
            results = chain.invoke({"content": chunk_text})
            
            if not results or not results.knowledge_list:
                log_proofreading_debug("チャンクから知識が抽出されませんでした")
                return []
            
            # 知識項目の後処理
            processed_knowledge: List[KnowledgeFromLatex] = []
            for knowledge in results.knowledge_list:
                # メタデータ設定
                knowledge.knowledge_type = knowledge_type.strip() if knowledge_type else None
                knowledge.reference_url = document_name
                
                # バリデーション
                if EXCLUDE_EMPTY_KNOWLEDGE and not self.validate_knowledge_item(knowledge):
                    continue
                
                processed_knowledge.append(knowledge)
                log_proofreading_debug(f"知識項目抽出: {knowledge.description[:50]}...")
            
            log_proofreading_info(f"チャンク知識抽出完了: {len(processed_knowledge)}個の知識項目")
            return processed_knowledge
            
        except Exception as e:
            raise KnowledgeExtractionError(f"チャンクからの知識抽出中にエラーが発生しました: {e}")
    
    def extract_knowledge_from_documents(self, chunks: List[Dict[str, Any]]) -> List[KnowledgeFromLatex]:
        """
        複数ドキュメントのチャンクから知識を抽出
        
        Args:
            chunks (List[Dict[str, Any]]): 処理対象のチャンクリスト
            各チャンクは以下の構造を持つ:
            - "name": ドキュメント名
            - "knowledge_type": 知識タイプ
            - "chunks": チャンクデータのリスト
            
        Returns:
            List[KnowledgeFromLatex]: 抽出された全知識項目の集約リスト
            
        Raises:
            KnowledgeExtractionError: 知識抽出に失敗した場合
        """
        try:
            log_proofreading_info(f"複数ドキュメントからの知識抽出開始: {len(chunks)}ドキュメント")
            
            all_knowledge: List[KnowledgeFromLatex] = []
            
            for document_data in chunks:
                if not all(key in document_data for key in ["name", "knowledge_type", "chunks"]):
                    raise KnowledgeExtractionError(
                        f"必要なキー (name, knowledge_type, chunks) が不足しています: {document_data.keys()}"
                    )
                
                document_name = document_data["name"]
                knowledge_type = document_data["knowledge_type"]
                document_chunks = document_data["chunks"]
                
                log_proofreading_debug(f"ドキュメント処理中: {document_name} ({len(document_chunks)}チャンク)")
                
                for chunk_data in document_chunks:
                    chunk_text = chunk_data["chunk_text"]
                    chunk_knowledge = self.process_chunk_to_knowledge(
                        chunk_text, document_name, knowledge_type
                    )
                    all_knowledge.extend(chunk_knowledge)
            
            # 重複除去
            filtered_knowledge = self.filter_duplicate_knowledge(all_knowledge)
            
            log_proofreading_info(
                f"複数ドキュメントからの知識抽出完了: {len(filtered_knowledge)}個の知識項目 "
                f"(重複除去前: {len(all_knowledge)}個)"
            )
            
            return filtered_knowledge
            
        except Exception as e:
            raise KnowledgeExtractionError(f"複数ドキュメント知識抽出中にエラーが発生しました: {e}")
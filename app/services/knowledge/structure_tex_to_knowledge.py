"""
LaTeX文書から構造化された知識を抽出するサービス

学術論文の校正に必要な具体的な指示・ルール・仕様を
LaTeX文書から自動抽出し、構造化データとして提供します。
"""
from typing import List, Dict, Any

from app.schemas.schemas import KnowledgeFromLatex
from app.services.knowledge.core.knowledge_extraction_engine import KnowledgeExtractionEngine
from app.services.shared.logging_utils import log_proofreading_info
from app.services.shared.exceptions import KnowledgeExtractionError


class KnowledgeExtractionService:
    """LaTeX知識抽出サービス"""
    
    def __init__(self):
        self.engine = KnowledgeExtractionEngine()
    
    def structure_tex_to_knowledge(self, chunks: List[Dict[str, Any]]) -> List[KnowledgeFromLatex]:
        """
        LaTeXチャンクから構造化ナレッジを抽出する
        
        学術論文の校正・体裁に関する具体的な指示やルールを
        LaTeX文書から抽出し、構造化データとして返します。
        
        Args:
            chunks (List[Dict[str, Any]]): 処理対象のチャンクリスト
            各チャンクは以下の構造を持つ:
            - "name": ドキュメント名
            - "knowledge_type": 知識タイプ（例: "学会フォーマット"）
            - "chunks": チャンクデータのリスト
                - "chunk_text": チャンクのテキスト内容
                - その他のメタデータ
                
        Returns:
            List[KnowledgeFromLatex]: 抽出された知識項目の集約リスト
            各知識項目は以下の情報を含む:
            - description: 知識の内容（具体的な指示・ルール）
            - knowledge_type: 知識の分類
            - reference_url: 参照元ドキュメント名
            - その他のメタデータ
            
        Raises:
            KnowledgeExtractionError: 知識抽出に失敗した場合
            
        Examples:
            抽出される知識の例:
            - "フォントサイズは10ポイントに設定"
            - "図のキャプションは図の下に配置"
            - "要約は200語以内に制限"
            - "引用は著者名と年を記載"
        """
        try:
            log_proofreading_info("LaTeX知識抽出処理を開始")
            return self.engine.extract_knowledge_from_documents(chunks)
        except Exception as e:
            raise KnowledgeExtractionError(f"LaTeX知識抽出中にエラーが発生しました: {e}")
    
    def process_document_chunk(
        self, 
        chunk_text: str, 
        document_name: str, 
        knowledge_type: str
    ) -> List[KnowledgeFromLatex]:
        """
        単一のドキュメントチャンクから知識を抽出
        
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
            log_proofreading_info("単一チャンクからの知識抽出を開始")
            return self.engine.process_chunk_to_knowledge(chunk_text, document_name, knowledge_type)
        except Exception as e:
            raise KnowledgeExtractionError(f"単一チャンク知識抽出中にエラーが発生しました: {e}")


# 下位互換性のためのサービスインスタンス
_service = KnowledgeExtractionService()

def structure_tex_to_knowledge(chunks: List[Dict[str, Any]]) -> List[KnowledgeFromLatex]:
    """
    下位互換性のための関数ラッパー
    
    Args:
        chunks (List[Dict[str, Any]]): 処理対象のチャンクリスト
        
    Returns:
        List[KnowledgeFromLatex]: 抽出された知識項目の集約リスト
    """
    return _service.structure_tex_to_knowledge(chunks)

def _process_document_chunk(
    chunk_text: str, 
    document_name: str, 
    knowledge_type: str
) -> List[KnowledgeFromLatex]:
    """
    下位互換性のための関数ラッパー
    
    Args:
        chunk_text (str): 処理対象のチャンクテキスト
        document_name (str): ドキュメント名
        knowledge_type (str): ナレッジタイプ
        
    Returns:
        List[KnowledgeFromLatex]: 抽出された知識項目リスト
    """
    return _service.process_document_chunk(chunk_text, document_name, knowledge_type)
"""
校正処理用のユーティリティ関数
"""
from typing import List, Dict, Any, Tuple
from app.schemas.schemas import ProofreadResult
from app.services.proofreading.config.proofreading_config import KNOWLEDGE_SEARCH_TOP_K

def format_knowledge_snippet(page_content: str, reference_url: str) -> str:
    """
    知識ベースの検索結果を整形する
    
    Args:
        page_content (str): ページコンテンツ
        reference_url (str): 参照URL
        
    Returns:
        str: 整形済みスニペット
    """
    return f"{page_content} (参照: {reference_url})"

def create_knowledge_block(cited_snippets: List[str]) -> str:
    """
    引用スニペットリストから知識ブロックを作成
    
    Args:
        cited_snippets (List[str]): 引用スニペットのリスト
        
    Returns:
        str: 整形済み知識ブロック
    """
    return "\n".join(cited_snippets)

def create_proofread_section_dict(
    result: ProofreadResult, 
    queries: List[str], 
    knowledge: str
) -> Dict[str, Any]:
    """
    校正結果から辞書形式のレスポンスを作成
    
    Args:
        result (ProofreadResult): 校正結果
        queries (List[str]): 使用したクエリ
        knowledge (str): 参照した知識
        
    Returns:
        Dict[str, Any]: レスポンス辞書
    """
    return {
        "pre_proofread": result.pre_proofread,
        "post_proofread": result.post_proofread,
        "description": result.description,
        "sentences": result.sentences,
        "queries": queries,
        "knowledge": knowledge
    }

def create_proofread_section_dict_without_knowledge(result: ProofreadResult) -> Dict[str, Any]:
    """
    校正結果から辞書形式のレスポンスを作成（知識ベースなし）
    
    Args:
        result (ProofreadResult): 校正結果
        
    Returns:
        Dict[str, Any]: レスポンス辞書
    """
    return {
        "pre_proofread": result.pre_proofread,
        "post_proofread": result.post_proofread,
        "description": result.description,
        "sentences": result.sentences,
        "queries": [],
        "knowledge": ""
    }

def get_search_parameters() -> Dict[str, int]:
    """
    検索パラメータを取得
    
    Returns:
        Dict[str, int]: 検索パラメータ
    """
    return {"k": KNOWLEDGE_SEARCH_TOP_K}
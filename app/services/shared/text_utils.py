"""
テキスト処理用のユーティリティ関数
"""
from typing import Union
from app.services.knowledge.config.chunking_config import SUPPORTED_ENCODINGS, FALLBACK_ENCODING
from app.services.shared.exceptions import ChunkingError


def ensure_string(data: Union[str, bytes]) -> str:
    """
    bytes → str を安全に変換（複数エンコーディング対応）
    
    Args:
        data (Union[str, bytes]): 変換対象のデータ
        
    Returns:
        str: 変換されたテキスト
        
    Raises:
        ChunkingError: 変換に失敗した場合
    """
    if isinstance(data, str):
        return data
    
    if not isinstance(data, bytes):
        raise ChunkingError(f"サポートされていないデータ型です: {type(data)}")
    
    for encoding in SUPPORTED_ENCODINGS:
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    
    # 最後の手段として置換復号を実行
    try:
        return data.decode(FALLBACK_ENCODING, errors="replace")
    except Exception as e:
        raise ChunkingError(f"テキスト変換に失敗しました: {e}")


def validate_text_length(text: str, min_length: int, max_length: int) -> None:
    """
    テキスト長の妥当性を検証
    
    Args:
        text (str): 検証対象のテキスト
        min_length (int): 最小長
        max_length (int): 最大長
        
    Raises:
        ChunkingError: テキスト長が範囲外の場合
    """
    if not text or not text.strip():
        raise ChunkingError("テキストが空です")
    
    text_length = len(text.strip())
    
    if text_length < min_length:
        raise ChunkingError(f"テキストが短すぎます (最小: {min_length}文字)")
    
    if text_length > max_length:
        raise ChunkingError(f"テキストが長すぎます (最大: {max_length}文字)")


def clean_chunk(chunk: str) -> str:
    """
    チャンクのクリーニング（空白の正規化等）
    
    Args:
        chunk (str): クリーニング対象のチャンク
        
    Returns:
        str: クリーニング済みチャンク
    """
    if not chunk:
        return ""
    
    # 先頭末尾の空白削除と、複数行の空白行を単一に
    cleaned = chunk.strip()
    cleaned = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned)
    
    return cleaned


import re
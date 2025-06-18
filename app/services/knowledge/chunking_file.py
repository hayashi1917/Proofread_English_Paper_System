"""
LaTeXファイルのチャンキング（文書分割）サービス

LaTeX文書を意味のある単位に分割し、後続の処理（校正、知識抽出等）に適した
形式に変換します。
"""
from typing import List, Dict, Any, Union

from app.services.knowledge.core.chunking_engine import ChunkingEngine
from app.services.shared.logging_utils import log_proofreading_info
from app.services.shared.exceptions import ChunkingError


class ChunkingService:
    """LaTeX文書チャンキングサービス"""
    
    def __init__(self, chunk_size: int = 2000, chunk_overlap: int = 100):
        """
        Args:
            chunk_size (int): チャンクサイズ
            chunk_overlap (int): チャンクオーバーラップサイズ
        """
        self.engine = ChunkingEngine(chunk_size, chunk_overlap)
    
    def split_latex_by_splitter(self, latex: Union[str, bytes]) -> List[str]:
        """
        LangChainのLatexTextSplitterを使用してLaTeXテキストを分割
        
        Args:
            latex (Union[str, bytes]): 分割対象のLaTeXテキスト
            
        Returns:
            List[str]: 分割されたチャンクのリスト
            
        Raises:
            ChunkingError: 分割処理に失敗した場合
        """
        try:
            log_proofreading_info("LangChain splitterによるLaTeX分割を開始")
            return self.engine.split_by_splitter(latex)
        except Exception as e:
            raise ChunkingError(f"LangChain splitter分割中にエラーが発生しました: {e}")
    
    def split_latex_by_section(self, latex: Union[str, bytes]) -> List[str]:
        """
        LaTeXセクション区切りでテキストを分割
        
        Args:
            latex (Union[str, bytes]): 分割対象のLaTeXテキスト
            
        Returns:
            List[str]: セクション単位で分割されたチャンクのリスト
            
        Raises:
            ChunkingError: 分割処理に失敗した場合
        """
        try:
            log_proofreading_info("セクション区切りによるLaTeX分割を開始")
            return self.engine.split_by_section(latex)
        except Exception as e:
            raise ChunkingError(f"セクション分割中にエラーが発生しました: {e}")
    
    def chunking_tex_files(self, tex_files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        複数のLaTeXファイルをチャンクに分割
        
        Args:
            tex_files (List[Dict[str, Any]]): 処理対象のファイルリスト
                各ファイルは以下のキーを持つ辞書:
                - "name": ファイル名
                - "content": LaTeXコンテンツ
                - "knowledge_type": 知識タイプ
                
        Returns:
            List[Dict[str, Any]]: チャンク分割されたファイルリスト
            各ファイルは以下の構造:
            - "name": ファイル名
            - "knowledge_type": 知識タイプ  
            - "chunks": チャンクメタデータのリスト
            - "total_chunks": 総チャンク数
            
        Raises:
            ChunkingError: 処理に失敗した場合
        """
        try:
            log_proofreading_info("複数LaTeXファイルのチャンク処理を開始")
            return self.engine.process_multiple_files(tex_files)
        except Exception as e:
            raise ChunkingError(f"複数ファイル処理中にエラーが発生しました: {e}")
    
    def chunking_tex_file(self, tex: str) -> List[str]:
        """
        単一のLaTeXファイルをチャンクに分割
        
        Args:
            tex (str): LaTeXソースコード
            
        Returns:
            List[str]: チャンク済み文字列のリスト
            
        Raises:
            ChunkingError: 分割処理に失敗した場合
        """
        try:
            log_proofreading_info("単一LaTeXファイルのチャンク処理を開始")
            return self.engine.split_by_section(tex)
        except Exception as e:
            raise ChunkingError(f"単一ファイル処理中にエラーが発生しました: {e}")


# 下位互換性のためのサービスインスタンス
_service = ChunkingService()

def split_latex_by_splitter(latex: Union[str, bytes]) -> List[str]:
    """
    下位互換性のための関数ラッパー
    """
    return _service.split_latex_by_splitter(latex)

def split_latex_by_section(latex: Union[str, bytes]) -> List[str]:
    """
    下位互換性のための関数ラッパー
    """
    return _service.split_latex_by_section(latex)

def chunking_tex_files(tex_files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    下位互換性のための関数ラッパー
    """
    return _service.chunking_tex_files(tex_files)

def chunking_tex_file(tex: str) -> List[str]:
    """
    下位互換性のための関数ラッパー
    """
    return _service.chunking_tex_file(tex)
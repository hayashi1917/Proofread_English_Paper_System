"""
LaTeXテキスト分割（チャンキング）エンジン
"""
from typing import List, Dict, Any, Union
from langchain_text_splitters import LatexTextSplitter

from app.services.shared.text_utils import ensure_string, validate_text_length, clean_chunk
from app.services.shared.logging_utils import log_proofreading_debug, log_proofreading_info
from app.services.knowledge.config.chunking_config import (
    DEFAULT_CHUNK_SIZE,
    DEFAULT_CHUNK_OVERLAP,
    SECTION_REGEX,
    DOCUMENT_START_MARKER,
    MIN_CHUNK_SIZE,
    MAX_CHUNK_SIZE
)
from app.services.shared.exceptions import ChunkingError


class ChunkingEngine:
    """LaTeX文書のチャンキング処理エンジン"""
    
    def __init__(self, chunk_size: int = DEFAULT_CHUNK_SIZE, chunk_overlap: int = DEFAULT_CHUNK_OVERLAP):
        """
        Args:
            chunk_size (int): チャンクサイズ
            chunk_overlap (int): チャンクオーバーラップサイズ
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.latex_splitter = LatexTextSplitter(
            chunk_size=chunk_size, 
            chunk_overlap=chunk_overlap
        )
    
    def split_by_splitter(self, latex: Union[str, bytes]) -> List[str]:
        """
        LangChainのLatexTextSplitterを使用してテキストを分割
        
        Args:
            latex (Union[str, bytes]): 分割対象のLaTeXテキスト
            
        Returns:
            List[str]: 分割されたチャンクのリスト
            
        Raises:
            ChunkingError: 分割処理に失敗した場合
        """
        try:
            text = ensure_string(latex)
            validate_text_length(text, MIN_CHUNK_SIZE, MAX_CHUNK_SIZE)
            
            log_proofreading_debug("LangChain splitterによる分割開始", {
                "text_length": len(text),
                "chunk_size": self.chunk_size,
                "chunk_overlap": self.chunk_overlap
            })
            
            chunks = self.latex_splitter.split_text(text)
            cleaned_chunks = [clean_chunk(chunk) for chunk in chunks if chunk.strip()]
            
            log_proofreading_info(f"LangChain splitterによる分割完了: {len(cleaned_chunks)}チャンク")
            return cleaned_chunks
            
        except Exception as e:
            raise ChunkingError(f"LangChain splitterによる分割中にエラーが発生しました: {e}")
    
    def split_by_section(self, latex: Union[str, bytes]) -> List[str]:
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
            text = ensure_string(latex)
            validate_text_length(text, MIN_CHUNK_SIZE, MAX_CHUNK_SIZE)
            
            log_proofreading_debug("セクション分割開始", {"text_length": len(text)})
            
            # ドキュメント開始以前の前文を除外
            doc_start = text.find(DOCUMENT_START_MARKER)
            if doc_start != -1:
                text = text[doc_start:]
                log_proofreading_debug("ドキュメント開始マーカー以前を除外", {"new_length": len(text)})
            
            # セクション区切りを検索
            matches = list(SECTION_REGEX.finditer(text))
            
            if not matches:
                log_proofreading_debug("セクションが見つからないため、全文を1チャンクとして返す")
                return [clean_chunk(text)]
            
            # セクション区切りでチャンクを作成
            chunks = []
            for i, match in enumerate(matches):
                start = match.start()
                end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
                chunk = text[start:end]
                cleaned_chunk = clean_chunk(chunk)
                if cleaned_chunk:
                    chunks.append(cleaned_chunk)
            
            log_proofreading_info(f"セクション分割完了: {len(chunks)}チャンク ({len(matches)}セクション検出)")
            return chunks
            
        except Exception as e:
            raise ChunkingError(f"セクション分割中にエラーが発生しました: {e}")
    
    def create_chunk_metadata(self, chunk: str, chunk_id: int, source_name: str = None) -> Dict[str, Any]:
        """
        チャンクのメタデータを作成
        
        Args:
            chunk (str): チャンクテキスト
            chunk_id (int): チャンクID
            source_name (str, optional): ソースファイル名
            
        Returns:
            Dict[str, Any]: チャンクメタデータ
        """
        metadata = {
            "chunk_id": chunk_id,
            "chunk_text": chunk,
            "chunk_length": len(chunk),
            "chunk_size_config": self.chunk_size,
            "overlap_config": self.chunk_overlap
        }
        
        if source_name:
            metadata["source_name"] = source_name
            
        return metadata
    
    def process_multiple_files(self, tex_files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        複数のLaTeXファイルを処理してチャンクに分割
        
        Args:
            tex_files (List[Dict[str, Any]]): 処理対象のファイルリスト
                各ファイルは "name", "content", "knowledge_type" キーを持つ辞書
                
        Returns:
            List[Dict[str, Any]]: チャンク分割されたファイルリスト
            
        Raises:
            ChunkingError: 処理に失敗した場合
        """
        try:
            log_proofreading_info(f"複数ファイルのチャンク処理開始: {len(tex_files)}ファイル")
            
            results = []
            for file_data in tex_files:
                if not all(key in file_data for key in ["name", "content", "knowledge_type"]):
                    raise ChunkingError(f"必要なキー (name, content, knowledge_type) が不足しています: {file_data.keys()}")
                
                file_name = file_data["name"]
                log_proofreading_debug(f"ファイル処理中: {file_name}")
                
                chunks = self.split_by_section(file_data["content"])
                
                chunk_metadata_list = [
                    self.create_chunk_metadata(chunk, i, file_name)
                    for i, chunk in enumerate(chunks)
                ]
                
                result = {
                    "name": file_name,
                    "knowledge_type": file_data["knowledge_type"],
                    "chunks": chunk_metadata_list,
                    "total_chunks": len(chunks)
                }
                results.append(result)
                
                log_proofreading_debug(f"ファイル処理完了: {file_name} → {len(chunks)}チャンク")
            
            log_proofreading_info(f"複数ファイルのチャンク処理完了: 合計{sum(r['total_chunks'] for r in results)}チャンク")
            return results
            
        except Exception as e:
            raise ChunkingError(f"複数ファイル処理中にエラーが発生しました: {e}")
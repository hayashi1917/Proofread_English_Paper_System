"""
NLP（自然言語処理）ベースのLaTeXテキスト分割エンジン

正規表現ベースの分割よりも高精度で簡潔な実装を提供します。
NLTK、LangChainを活用した高性能な文書分割機能。
"""
from typing import List, Dict, Any, Union
import re

# NLP libraries
import nltk
from nltk.tokenize import sent_tokenize
from langchain.text_splitter import RecursiveCharacterTextSplitter

from app.services.shared.text_utils import ensure_string, validate_text_length, clean_chunk
from app.services.shared.logging_utils import log_proofreading_debug, log_proofreading_info
from app.services.knowledge.config.chunking_config import (
    DEFAULT_CHUNK_SIZE,
    DEFAULT_CHUNK_OVERLAP,
    MIN_CHUNK_SIZE,
    MAX_CHUNK_SIZE
)
from app.services.shared.exceptions import ChunkingError


class NLPChunkingEngine:
    """NLPベースのLaTeX文書チャンキングエンジン"""
    
    def __init__(self, chunk_size: int = DEFAULT_CHUNK_SIZE, chunk_overlap: int = DEFAULT_CHUNK_OVERLAP):
        """
        Args:
            chunk_size (int): チャンクサイズ
            chunk_overlap (int): チャンクオーバーラップサイズ
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # LangChain文分割器の初期化
        self.sentence_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=[". ", "! ", "? ", "\n\n", "\n", " "],
            length_function=len,
            is_separator_regex=False
        )
        
        # NLTK punkt tokenizerのダウンロード確認
        self._ensure_nltk_data()
    
    def _ensure_nltk_data(self):
        """NLTK必要データのダウンロード確認"""
        try:
            nltk.data.find('tokenizers/punkt_tab')
        except LookupError:
            log_proofreading_info("NLTKデータをダウンロード中...")
            nltk.download('punkt_tab', quiet=True)
            nltk.download('punkt', quiet=True)
    
    def split_by_sentence_nlp(self, latex: Union[str, bytes]) -> List[str]:
        """
        NLTKの文分割機能を使用してテキストを文単位で分割
        
        正規表現ベースより高精度で、学術論文特有の文構造も適切に処理します。
        
        Args:
            latex (Union[str, bytes]): 分割対象のLaTeXテキスト
            
        Returns:
            List[str]: 文単位で分割されたチャンクのリスト
            
        Raises:
            ChunkingError: 分割処理に失敗した場合
        """
        try:
            text = ensure_string(latex)
            validate_text_length(text, MIN_CHUNK_SIZE, MAX_CHUNK_SIZE, skip_max_validation=True)
            
            log_proofreading_debug("NLP文単位分割開始", {"text_length": len(text)})
            
            # LaTeX環境とコマンドを一時的に保護
            protected_text, protection_map = self._protect_latex_elements(text)
            
            # NLTKによる高精度文分割
            sentences = sent_tokenize(protected_text)
            
            # LaTeX要素を復元
            restored_chunks = []
            for sentence in sentences:
                restored = self._restore_latex_elements(sentence, protection_map)
                cleaned = clean_chunk(restored)
                if cleaned:
                    restored_chunks.append(cleaned)
            
            log_proofreading_info(f"NLP文単位分割完了: {len(restored_chunks)}チャンク")
            return restored_chunks
            
        except Exception as e:
            raise ChunkingError(f"NLP文単位分割中にエラーが発生しました: {e}")
    
    def split_by_command_nlp(self, latex: Union[str, bytes]) -> List[str]:
        """
        LaTeXコマンド構造を理解したNLPベースコマンド分割
        
        単純な正規表現ではなく、LaTeX文法を考慮した構造的分割を行います。
        
        Args:
            latex (Union[str, bytes]): 分割対象のLaTeXテキスト
            
        Returns:
            List[str]: コマンド単位で分割されたチャンクのリスト
            
        Raises:
            ChunkingError: 分割処理に失敗した場合
        """
        try:
            text = ensure_string(latex)
            validate_text_length(text, MIN_CHUNK_SIZE, MAX_CHUNK_SIZE, skip_max_validation=True)
            
            log_proofreading_debug("NLPコマンド分割開始", {"text_length": len(text)})
            
            chunks = []
            current_pos = 0
            
            # LaTeX構造パターン（優先度順）
            latex_patterns = [
                r'\\documentclass(?:\[[^\]]*\])?\{[^}]*\}',      # documentclass
                r'\\usepackage(?:\[[^\]]*\])?\{[^}]*\}',        # usepackage
                r'\\begin\{[^}]+\}.*?\\end\{[^}]+\}',           # 環境
                r'\\[a-zA-Z*]+(?:\[[^\]]*\])?(?:\{[^{}]*\})*',  # その他コマンド
            ]
            
            for pattern in latex_patterns:
                for match in re.finditer(pattern, text[current_pos:], re.DOTALL):
                    actual_start = current_pos + match.start()
                    actual_end = current_pos + match.end()
                    
                    # コマンド前のテキスト
                    before_text = text[current_pos:actual_start].strip()
                    if before_text:
                        chunks.append(clean_chunk(before_text))
                    
                    # コマンド自体
                    command_text = match.group(0)
                    chunks.append(clean_chunk(command_text))
                    
                    current_pos = actual_end
            
            # 残りのテキスト
            remaining = text[current_pos:].strip()
            if remaining:
                chunks.append(clean_chunk(remaining))
            
            # 空チャンクを除去
            cleaned_chunks = [chunk for chunk in chunks if chunk]
            
            log_proofreading_info(f"NLPコマンド分割完了: {len(cleaned_chunks)}チャンク")
            return cleaned_chunks
            
        except Exception as e:
            raise ChunkingError(f"NLPコマンド分割中にエラーが発生しました: {e}")
    
def split_by_command_nlp(self, latex: Union[str, bytes]) -> List[str]:
    """
    LaTeXコマンド構造を理解したNLPベースコマンド分割
    
    単純な正規表現ではなく、LaTeX文法を考慮した構造的分割を行います。
    
    Args:
        latex (Union[str, bytes]): 分割対象のLaTeXテキスト
        
    Returns:
        List[str]: コマンド単位で分割されたチャンクのリスト
        
    Raises:
        ChunkingError: 分割処理に失敗した場合
    """
    try:
        text = ensure_string(latex)
        validate_text_length(text, MIN_CHUNK_SIZE, MAX_CHUNK_SIZE, skip_max_validation=True)
        
        log_proofreading_debug("NLPコマンド分割開始", {"text_length": len(text)})
        
        # LaTeX構造パターン（優先度順）
        latex_patterns = [
            (r'\\documentclass(?:\[[^\]]*\])?\{[^}]*\}', 'documentclass'),
            (r'\\usepackage(?:\[[^\]]*\])?\{[^}]*\}', 'usepackage'),
            (r'\\begin\{[^}]+\}.*?\\end\{[^}]+\}', 'environment'),
            (r'\\[a-zA-Z*]+(?:\[[^\]]*\])?(?:\{[^{}]*\})*', 'command'),
        ]
        
        # すべてのマッチを収集
        all_matches = []
        for pattern, pattern_type in latex_patterns:
            for match in re.finditer(pattern, text, re.DOTALL):
                all_matches.append({
                    'start': match.start(),
                    'end': match.end(),
                    'text': match.group(0),
                    'type': pattern_type,
                    'priority': latex_patterns.index((pattern, pattern_type))
                })
        
        # 位置でソート
        all_matches.sort(key=lambda x: x['start'])
        
        # 重複を除去（より優先度の高いパターンを残す）
        filtered_matches = []
        i = 0
        while i < len(all_matches):
            current_match = all_matches[i]
            
            # 現在のマッチと重複する後続のマッチを探す
            overlapping = []
            j = i
            while j < len(all_matches) and all_matches[j]['start'] < current_match['end']:
                overlapping.append(all_matches[j])
                j += 1
            
            # 重複する中で最も優先度の高いものを選択
            best_match = min(overlapping, key=lambda x: x['priority'])
            filtered_matches.append(best_match)
            
            # 選択したマッチの終了位置以降から再開
            while i < len(all_matches) and all_matches[i]['start'] < best_match['end']:
                i += 1
        
        # チャンクを生成
        chunks = []
        current_pos = 0
        
        for match in filtered_matches:
            # マッチ前のテキスト
            before_text = text[current_pos:match['start']].strip()
            if before_text:
                chunks.append(clean_chunk(before_text))
            
            # マッチしたコマンド/環境
            chunks.append(clean_chunk(match['text']))
            current_pos = match['end']
        
        # 残りのテキスト
        remaining = text[current_pos:].strip()
        if remaining:
            chunks.append(clean_chunk(remaining))
        
        # 空チャンクを除去
        cleaned_chunks = [chunk for chunk in chunks if chunk]
        
        log_proofreading_info(f"NLPコマンド分割完了: {len(cleaned_chunks)}チャンク")
        return cleaned_chunks
        
    except Exception as e:
        raise ChunkingError(f"NLPコマンド分割中にエラーが発生しました: {e}")
    
    def split_by_recursive_nlp(self, latex: Union[str, bytes]) -> List[str]:
        """
        LangChainの高性能RecursiveCharacterTextSplitterを使用した分割
        
        Args:
            latex (Union[str, bytes]): 分割対象のLaTeXテキスト
            
        Returns:
            List[str]: 分割されたチャンクのリスト
            
        Raises:
            ChunkingError: 分割処理に失敗した場合
        """
        try:
            text = ensure_string(latex)
            validate_text_length(text, MIN_CHUNK_SIZE, MAX_CHUNK_SIZE, skip_max_validation=True)
            
            log_proofreading_debug("LangChain再帰的分割開始", {"text_length": len(text)})
            
            chunks = self.sentence_splitter.split_text(text)
            cleaned_chunks = [clean_chunk(chunk) for chunk in chunks if chunk.strip()]
            
            log_proofreading_info(f"LangChain再帰的分割完了: {len(cleaned_chunks)}チャンク")
            return cleaned_chunks
            
        except Exception as e:
            raise ChunkingError(f"LangChain再帰的分割中にエラーが発生しました: {e}")
    
    def _protect_latex_elements(self, text: str) -> tuple[str, Dict[str, str]]:
        """LaTeX環境とコマンドを一時的に保護"""
        protection_map = {}
        protected_text = text
        placeholder_counter = 0
        
        # LaTeX環境を保護
        env_pattern = r'\\begin\{[^}]+\}.*?\\end\{[^}]+\}'
        for match in re.finditer(env_pattern, text, re.DOTALL):
            placeholder = f"__LATEX_ENV_{placeholder_counter}__"
            protection_map[placeholder] = match.group(0)
            protected_text = protected_text.replace(match.group(0), placeholder)
            placeholder_counter += 1
        
        # インラインコマンドを保護
        inline_pattern = r'\\[a-zA-Z*]+(?:\[[^\]]*\])?(?:\{[^{}]*\})*'
        for match in re.finditer(inline_pattern, protected_text):
            placeholder = f"__LATEX_CMD_{placeholder_counter}__"
            protection_map[placeholder] = match.group(0)
            protected_text = protected_text.replace(match.group(0), placeholder)
            placeholder_counter += 1
        
        return protected_text, protection_map
    
    def _restore_latex_elements(self, text: str, protection_map: Dict[str, str]) -> str:
        """保護されたLaTeX要素を復元"""
        restored = text
        for placeholder, original in protection_map.items():
            restored = restored.replace(placeholder, original)
        return restored
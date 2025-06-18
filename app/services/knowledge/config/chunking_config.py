"""
テキスト分割（チャンキング）処理の設定値
"""
import re

# LaTeX分割の設定
DEFAULT_CHUNK_SIZE = 2000
DEFAULT_CHUNK_OVERLAP = 100

# セクション検出の正規表現
SECTION_REGEX = re.compile(
    r'\\(?:section)\*?\s*{[^}]*}',
    flags=re.IGNORECASE
)

# ドキュメント処理の設定
DOCUMENT_START_MARKER = r"\begin{document}"

# エンコーディング設定
SUPPORTED_ENCODINGS = ["utf-8", "utf-8-sig", "shift_jis", "cp932"]
FALLBACK_ENCODING = "utf-8"

# チャンク最小・最大サイズ
MIN_CHUNK_SIZE = 10
MAX_CHUNK_SIZE = 10000

# ログ出力設定
CHUNKING_DEBUG_ENABLED = True
"""
英語論文校正サービスの設定値
"""
import os
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv(".env.local")

# 環境変数設定
ENV_FILE_PATH = ".env.local"
ENGLISH_PAPER_FOLDER_ID_KEY = "ENGLISH_PAPER_BEFORE_PROOFREADING_FOLDER_ID"

# デフォルト設定
DEFAULT_KNOWLEDGE_MODE = True
DEFAULT_CHUNK_SIZE = 2000
DEFAULT_CHUNK_OVERLAP = 100

# バリデーション設定
MIN_TEX_FILE_SIZE = 10  # bytes
MAX_TEX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# 校正モード
class ProofreadingMode:
    WITH_KNOWLEDGE = "with_knowledge"
    WITHOUT_KNOWLEDGE = "without_knowledge"

# 分割モード
class SplitMode:
    SECTION = "section"
    COMMAND = "command"
    SENTENCE = "sentence"
    HYBRID = "hybrid"
    RECURSIVE_NLP = "recursive_nlp"

# ログ出力設定
PROOFREADING_PAPER_DEBUG_ENABLED = True
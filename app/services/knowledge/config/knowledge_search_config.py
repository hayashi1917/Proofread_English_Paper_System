"""
知識検索サービスの設定値
"""

# 検索パラメータのデフォルト値
DEFAULT_SEARCH_LIMIT = 10
DEFAULT_SIMILARITY_THRESHOLD = 0.7

# 検索の種類
class SearchType:
    GENERAL = "general"
    BY_ISSUE_CATEGORY = "by_issue_category"  
    BY_KNOWLEDGE_TYPE = "by_knowledge_type"

# キャッシュ設定
ENABLE_SEARCH_CACHE = False
CACHE_EXPIRY_SECONDS = 300  # 5分

# バリデーション設定
MIN_QUERY_LENGTH = 1
MAX_QUERY_LENGTH = 1000

# ログ出力設定
KNOWLEDGE_SEARCH_DEBUG_ENABLED = True
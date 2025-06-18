"""
Google Drive API操作の設定値
"""

# ページネーション設定
DEFAULT_PAGE_SIZE = 1000
MAX_PAGE_SIZE = 1000

# ファイルタイプとナレッジタイプのマッピング
KNOWLEDGE_TYPE_MAPPING = {
    "tex": "学会フォーマット",
    "pdf": "一般的な論文"
}

# 検索クエリテンプレート
FOLDER_QUERY_TEMPLATE = "'{folder_id}' in parents"
PDF_FOLDER_QUERY_TEMPLATE = "'{folder_id}' in parents and mimeType='application/pdf'"

# リクエスト設定
FILES_FIELDS = "files(id,name,mimeType),nextPageToken"

# ログ出力設定
GOOGLE_DRIVE_DEBUG_ENABLED = True
# 現在の有効なAPIエンドポイント一覧

## ナレッジパイプライン関連

### `/knowledge_pipeline/`

| メソッド | エンドポイント | 説明 | パラメータ |
|----------|---------------|------|------------|
| POST | `/` | TeX ファイルからナレッジ抽出 | なし |
| POST | `/from_pdf` | PDFファイルからナレッジ抽出（メイン） | `pdf_folder_id`, `use_page_splitting=true`, `use_enhanced_cache=true` |

### 強化キャッシュ管理

| メソッド | エンドポイント | 説明 |
|----------|---------------|------|
| GET | `/enhanced_cache/stats` | 詳細キャッシュ統計 |
| GET | `/enhanced_cache/recommendations` | キャッシュ最適化推奨事項 |
| POST | `/enhanced_cache/cleanup` | 条件付きキャッシュクリーンアップ |

### 診断機能

| メソッド | エンドポイント | 説明 |
|----------|---------------|------|
| GET | `/diagnose_folder/{folder_id}` | Google Driveフォルダ構成診断 |

## 英語論文校正関連

### `/proofread_english_paper/`
- 英語論文の校正処理エンドポイント

## 文書分析関連

### `/analyze_document/`
- Document Intelligence による文書分析

## データベース操作関連

### `/store_and_search_db/`
- ベクトルデータベースの操作

---

## 削除されたエンドポイント

### 重複していたPDFエンドポイント
- ❌ `/from_pdf_with_page_splitting` → `/from_pdf` で統合
- ❌ `/from_pdf_with_enhanced_cache` → `/from_pdf` で統合

### 旧キャッシュエンドポイント
- ❌ `/cache/stats` → `/enhanced_cache/stats` で代替
- ❌ `/cache/files` → 強化キャッシュで不要
- ❌ `/cache/cleanup` → `/enhanced_cache/cleanup` で代替

### テスト用エンドポイント
- ❌ `/latex_split_test/*` → 本機能では未使用

---

## メインの使用方法

**推奨:** PDFからナレッジ抽出
```bash
POST /knowledge_pipeline/from_pdf
{
    "pdf_folder_id": "optional",
    "use_page_splitting": true,    # ページ分割処理
    "use_enhanced_cache": true     # 強化キャッシュ（コスト削減）
}
```

**キャッシュ統計確認:**
```bash
GET /knowledge_pipeline/enhanced_cache/stats
```

**フォルダ診断:**
```bash
GET /knowledge_pipeline/diagnose_folder/{folder_id}
```
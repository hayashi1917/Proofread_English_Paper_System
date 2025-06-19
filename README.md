# 英語論文校正システム (pro_con_b4)

## 概要

このシステムは、LaTeX形式で書かれた英語論文を自動校正するためのAIベースのWebアプリケーションです。知識ベースと大規模言語モデル（LLM）を組み合わせて、論文の品質向上を支援します。

## 主な機能

### 1. 英語論文校正システム
- **ファイルアップロード機能**: `.tex`ファイルをドラッグ&ドロップまたはファイル選択で処理
- **知識ベース連携校正**: 蓄積された知識を参照して高精度な校正を実施
- **HyDE（Hypothetical Document Embeddings）**: 仮想的な文書埋め込みを生成してより適切な知識を検索
- **リアルタイム処理**: Webインターフェースで校正結果をリアルタイム表示

### 2. 知識管理システム
- **自動知識抽出**: LaTeX/PDFファイルから論文執筆に関する知識を自動抽出
- **ベクトル検索**: ChromaDBを使用した意味的類似性検索
- **知識カテゴリー分類**: 段落構成、文法、単語、形式の4カテゴリーで分類
- **Google Drive連携**: Google Driveから文書を自動取得・処理

### 3. 文書解析システム
- **Azure Document Intelligence**: PDFの高精度なテキスト抽出
- **多様な分割方式**: セクション、コマンド、文単位、ハイブリッド、NLP分割に対応
- **キャッシュ機能**: 処理済み文書のキャッシュによる高速化

## システム構成

### アーキテクチャ概要
```
[Webインターフェース] 
    ↓
[FastAPI アプリケーション]
    ↓
[校正パイプライン] ← [知識パイプライン]
    ↓                    ↓
[Azure OpenAI]     [ChromaDB ベクトルDB]
    ↓                    ↓
[校正結果]          [知識ベース]
```

### 技術スタック
- **バックエンド**: FastAPI (Python 3.12)
- **AI/ML**: Azure OpenAI (GPT-4o-mini), LangChain
- **データベース**: ChromaDB (ベクトルデータベース)
- **文書解析**: Azure Document Intelligence
- **フロントエンド**: HTML/CSS/JavaScript
- **外部連携**: Google Drive API
- **依存関係管理**: Poetry
- **コンテナ**: Docker

## セットアップ

### 必要な環境
- Python 3.12以上
- Poetry
- Azure OpenAI アカウント
- Azure Document Intelligence アカウント
- Google Drive API 認証情報

### インストール手順

1. **リポジトリのクローン**
```bash
git clone <repository-url>
cd pro_con_b4
```

2. **依存関係のインストール**
```bash
poetry install
```

3. **環境変数の設定**
`.env.local`ファイルを作成し、以下の環境変数を設定:

```bash
# Azure OpenAI 設定
AZURE_OPENAI_KEY=your_openai_key_here
AZURE_OPENAI_ENDPOINT=your_openai_endpoint_here

# Azure Document Intelligence 設定
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=your_document_intelligence_endpoint_here
AZURE_DOCUMENT_INTELLIGENCE_KEY=your_document_intelligence_key_here

# Google Drive 設定
ENGLISH_PAPER_BEFORE_PROOFREADING_FOLDER_ID=your_folder_id_here
TEST_FOLDER_ID=your_test_folder_id_here
```

4. **Google Drive認証**
```bash
# credentials.json と token.json を配置
# Google Drive API の認証情報が必要
```

### アプリケーションの起動

```bash
# 開発サーバーの起動
uvicorn app.main:app --reload

# 本番環境用
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

アプリケーションは `http://localhost:8000` でアクセス可能です。

### Docker使用時

```bash
# イメージのビルド
docker build -t pro_con_b4 .

# コンテナの実行
docker run -p 8000:80 --env-file .env.local pro_con_b4
```

## API エンドポイント

### 校正関連エンドポイント

#### `/proofread_english_paper/file` (POST)
英語論文ファイルの校正を実行

**リクエスト**: 
- `file`: `.tex`ファイル（multipart/form-data）

**レスポンス**:
```json
[
  {
    "pre_proofread": "元のテキスト",
    "post_proofread": "校正後のテキスト", 
    "description": "校正理由",
    "sentences": ["関連する英文のリスト"]
  }
]
```

#### `/proofread_english_paper/without_knowledge` (POST)
知識ベースを使わない校正

**リクエスト**: 
- `file`: `.tex`ファイル

**レスポンス**: 上記と同様

### 知識管理エンドポイント

#### `/knowledge_pipeline/` (POST)
Google Driveから知識抽出パイプラインを実行

#### `/knowledge_pipeline/from_pdf` (POST)
PDFファイルから知識を抽出

**パラメータ**:
- `pdf_folder_id`: Google DriveのPDFフォルダID（オプション）

#### `/knowledge_pipeline/cache/stats` (GET)
Document Intelligenceキャッシュの統計情報を取得

### 文書解析エンドポイント

#### `/analyze_document/` (POST)
文書解析機能

#### `/store_and_search_db/` (POST)
ベクトルデータベースの検索機能

#### `/latex_split_test/` (POST)
LaTeX分割テスト機能

## プロジェクト構造

```
pro_con_b4/
├── app/
│   ├── api/                    # API層
│   │   ├── api.py             # APIルーター統合
│   │   └── routes/            # エンドポイント定義
│   │       ├── proofread_english_paper.py
│   │       ├── knowledge_pipeline.py
│   │       ├── analyze_document.py
│   │       ├── store_and_search_db.py
│   │       └── latex_split_test.py
│   ├── services/              # ビジネスロジック層
│   │   ├── knowledge/         # 知識管理サービス
│   │   │   ├── config/        # 設定ファイル
│   │   │   ├── core/          # コアエンジン
│   │   │   ├── prompts/       # LLMプロンプト
│   │   │   └── utils/         # ユーティリティ
│   │   ├── proofreading/      # 校正サービス
│   │   │   ├── config/        # 設定ファイル
│   │   │   ├── core/          # コアエンジン
│   │   │   ├── prompts/       # LLMプロンプト
│   │   │   └── utils/         # ユーティリティ
│   │   └── shared/            # 共通サービス
│   ├── schemas/               # Pydanticモデル
│   └── main.py               # FastAPIアプリケーション
├── libs/
│   └── azure_client.py       # Azureクライアント
├── static/
│   └── index.html           # Webインターフェース
├── chroma_db/               # ChromaDBデータ
├── document_intelligence_cache/  # キャッシュデータ
├── output/                  # 知識抽出結果
├── pyproject.toml          # Poetry設定
├── Dockerfile              # Docker設定
└── CLAUDE.md              # プロジェクト情報
```

## 使用方法

### 1. 論文校正の実行

1. Webブラウザで `http://localhost:8000` にアクセス
2. `.tex`ファイルをドラッグ&ドロップまたはファイル選択
3. 自動的に校正処理が開始
4. 校正結果が画面に表示

### 2. 知識ベースの構築

```bash
# APIを使用して知識抽出を実行
curl -X POST "http://localhost:8000/knowledge_pipeline/"

# または特定のPDFフォルダから抽出
curl -X POST "http://localhost:8000/knowledge_pipeline/from_pdf?pdf_folder_id=your_folder_id"
```

### 3. 分割テストの実行

LaTeX文書の最適な分割方式をテスト:

```bash
curl -X POST "http://localhost:8000/latex_split_test/compare" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@your_paper.tex"
```

## 設定とカスタマイズ

### 知識抽出設定

`app/services/knowledge/config/knowledge_extraction_config.py`:
```python
KNOWLEDGE_EXTRACTION_TIMEOUT = 30  # タイムアウト秒数
KNOWLEDGE_EXTRACTION_RETRY_COUNT = 3  # リトライ回数
MIN_KNOWLEDGE_DESCRIPTION_LENGTH = 5  # 最小知識記述長
```

### 校正設定

`app/services/proofreading/config/proofreading_paper_config.py`:
```python
# 分割モードの設定
class SplitMode(Enum):
    SECTION = "section"
    COMMAND = "command"
    SENTENCE = "sentence"
    HYBRID = "hybrid"
    RECURSIVE_NLP = "recursive_nlp"
```

### HyDE設定

`app/services/proofreading/config/hyde_config.py`:
- 仮想文書生成のためのプロンプト設定
- 検索クエリ生成パラメータ

## トラブルシューティング

### よくある問題

1. **Azure認証エラー**
   - `.env.local`ファイルのAzure認証情報を確認
   - エンドポイントURLの形式を確認

2. **Google Drive認証エラー**
   - `credentials.json`と`token.json`の配置を確認
   - Google Drive APIが有効になっているか確認

3. **ファイル処理エラー**
   - LaTeXファイルの文字エンコーディングを確認（UTF-8推奨）
   - ファイルサイズ制限を確認

4. **ChromaDBエラー**
   - `chroma_db/`ディレクトリの権限を確認
   - データベースの初期化が必要な場合は該当ディレクトリを削除

### ログ確認

```bash
# アプリケーションログの確認
tail -f logs/app.log

# デバッグモードでの起動
uvicorn app.main:app --reload --log-level debug
```

## 開発者向け情報

### コードスタイル

- Python 3.12の機能を活用
- 型ヒントの使用を推奨
- Pydanticモデルによるデータ検証
- ログ出力による処理追跡

### テスト

```bash
# テストの実行（テストファイルが存在する場合）
poetry run pytest

# 特定のテストファイル
poetry run pytest tests/unit/test_knowledge.py
```

### コントリビューション

1. フィーチャーブランチを作成
2. 変更を実装
3. テストを追加/更新
4. プルリクエストを作成

## ライセンス

このプロジェクトのライセンス情報については、リポジトリのLICENSEファイルを参照してください。

## 更新履歴

- **v0.1.0**: 初期リリース
  - 基本的な校正機能
  - 知識ベース管理
  - Webインターフェース

## サポート

問題や質問がある場合は、GitHubのIssuesページで報告してください。

---

**注意**: このシステムは研究・学習目的で開発されており、商用利用前には十分なテストと検証を行ってください。
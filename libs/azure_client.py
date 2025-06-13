from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
from langchain_openai import ChatOpenAI
import openai
import os
from typing import List, Dict, Any
from langchain.tools import BaseTool
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from app.services.utils.document_intelligence_cache import DocumentIntelligenceCache

load_dotenv(".env.local")

class AzureDocumentIntelligenceClient:
    def __init__(self, enable_cache: bool = True) -> None:
        self.client = DocumentIntelligenceClient(
            endpoint=os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT"),
            credential=AzureKeyCredential(os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")),
        )
        
        # キャッシュシステムを初期化
        self.cache = DocumentIntelligenceCache() if enable_cache else None
        
    def analyze_document_client(self) -> DocumentIntelligenceClient:
        return self.client
    
    def analyze_pdf_pages(self, file_bytes: bytes, file_name: str) -> List[Dict[str, Any]]:
        """
        PDFをページごとに分析してコンテンツを抽出する（キャッシュ機能付き）
        
        Args:
            file_bytes: PDFファイルのバイトデータ
            file_name: ファイル名（参照用）
            
        Returns:
            List[Dict]: ページごとのコンテンツとメタデータ
        """
        # キャッシュが有効で、キャッシュが存在する場合は取得
        if self.cache and self.cache.has_cache(file_bytes, file_name):
            cached_result = self.cache.get_cache(file_bytes, file_name)
            if cached_result is not None:
                return cached_result
        
        print(f"Document Intelligence で処理中: {file_name}")
        
        # PDFを分析してページごとの内容を取得
        poller = self.client.begin_analyze_document(
            model_id="prebuilt-read",
            body=file_bytes,
            output_content_format="markdown",
        )
        result = poller.result()
        
        # ページごとの情報を抽出
        pages_content = []
        if hasattr(result, 'pages') and result.pages:
            for i, page in enumerate(result.pages):
                page_content = ""
                
                # ページ内のパラグラフ（テキストブロック）を結合
                if hasattr(page, 'lines') and page.lines:
                    for line in page.lines:
                        if hasattr(line, 'content'):
                            page_content += line.content + "\n"
                
                # ページにコンテンツがある場合のみ追加
                if page_content.strip():
                    pages_content.append({
                        "page_number": i + 1,
                        "content": page_content.strip(),
                        "source_file": file_name
                    })
        
        # もしページ分けが取得できない場合は、全体のコンテンツを使用
        if not pages_content and hasattr(result, 'content'):
            pages_content.append({
                "page_number": 1,
                "content": result.content,
                "source_file": file_name
            })
        
        # 結果をキャッシュに保存
        if self.cache:
            self.cache.save_cache(file_bytes, file_name, pages_content)
        
        return pages_content
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        キャッシュの統計情報を取得
        
        Returns:
            キャッシュの統計情報、キャッシュが無効の場合はNone
        """
        if self.cache:
            return self.cache.get_cache_stats()
        return {"cache_enabled": False}
    
    def list_cached_files(self) -> List[Dict[str, Any]]:
        """
        キャッシュされたファイルの一覧を取得
        
        Returns:
            キャッシュファイルの情報リスト、キャッシュが無効の場合は空リスト
        """
        if self.cache:
            return self.cache.list_cached_files()
        return []
    
    def cleanup_old_cache(self, days: int = 30):
        """
        古いキャッシュファイルを削除
        
        Args:
            days: 保持期間（日数）
        """
        if self.cache:
            self.cache.cleanup_old_cache(days)      

class AzureOpenAIClient:
    def __init__(self,tools: List[BaseTool] | None = None):
        # ★ 1) max_completion_tokens で“書き過ぎ”ブロック
        # ★ 2) tools / tool_choice をその場で bind できるようにする
        self.client = ChatOpenAI(
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            model_name="gpt-4.1-mini",
            temperature=0,
            max_completion_tokens=4096,
        )
        if tools:                          # tools が渡されていたら即 bind
            self.client = self.client.bind(
                tools=tools,
                tool_choice="auto"
            )

    def get_openai_client(self) -> ChatOpenAI:
        return self.client

class AzureOpenAIEmbeddings:
    def __init__(self):
        self.client = OpenAIEmbeddings(
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            model="text-embedding-ada-002",
        )

    def get_openai_embeddings(self) -> OpenAIEmbeddings:
        return self.client


class ChromaDBClient:
    def __init__(self):
        azure_embeddings_client = AzureOpenAIEmbeddings()
        self.client = Chroma(
            collection_name="knowledge_base_db",
            persist_directory="chroma_db",
            embedding_function=azure_embeddings_client.get_openai_embeddings(),
        )

    def get_chroma_client(self) -> Chroma:
        return self.client

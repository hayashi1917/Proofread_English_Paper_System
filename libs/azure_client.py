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
from app.services.knowledge.utils.document_intelligence_cache import DocumentIntelligenceCache
from app.services.knowledge.utils.enhanced_cache_system import EnhancedDocumentIntelligenceCache

load_dotenv(".env.local")

class AzureDocumentIntelligenceClient:
    def __init__(self, enable_cache: bool = True, use_enhanced_cache: bool = True) -> None:
        self.client = DocumentIntelligenceClient(
            endpoint=os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT"),
            credential=AzureKeyCredential(os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")),
        )
        
        # キャッシュシステムを初期化
        if enable_cache:
            if use_enhanced_cache:
                self.cache = EnhancedDocumentIntelligenceCache()
                self.cache_type = "enhanced"
            else:
                self.cache = DocumentIntelligenceCache()
                self.cache_type = "legacy"
        else:
            self.cache = None
            self.cache_type = "disabled"
        
    def analyze_document_client(self) -> DocumentIntelligenceClient:
        return self.client
    
    def analyze_pdf_pages(self, file_bytes: bytes, file_name: str) -> List[Dict[str, Any]]:
        """
        PDFをページごとに分析してコンテンツを抽出する（キャッシュ機能付き・真のページ分割対応）
        
        Args:
            file_bytes: PDFファイルのバイトデータ
            file_name: ファイル名（参照用）
            
        Returns:
            List[Dict]: ページごとのコンテンツとメタデータ
        """
        from app.services.knowledge.utils.pdf_page_splitter import PDFPageSplitter
        
        # キャッシュが有効で、キャッシュが存在する場合は取得
        if self.cache and self.cache.has_cache(file_bytes, file_name):
            cached_result = self.cache.get_cache(file_bytes, file_name)
            if cached_result is not None:
                return cached_result
        
        print(f"Document Intelligence で複数ページ処理中: {file_name}")
        
        # PDFを物理的にページごとに分割
        splitter = PDFPageSplitter()
        pdf_info = splitter.get_pdf_info(file_bytes)
        print(f"PDF情報: {pdf_info['page_count']} ページ - {file_name}")
        
        # PDFを個別ページに分割
        pages_data = splitter.split_pdf_to_pages(file_bytes, file_name)
        
        # 各ページを個別に Document Intelligence で処理
        pages_content = []
        for page_data in pages_data:
            page_number = page_data["page_number"]
            page_bytes = page_data["page_bytes"]
            page_file_name = page_data["page_file_name"]
            
            print(f"ページ {page_number} を Document Intelligence で処理中...")
            
            try:
                # 個別ページを Document Intelligence で分析
                poller = self.client.begin_analyze_document(
                    model_id="prebuilt-read",
                    body=page_bytes,
                    output_content_format="markdown",
                )
                result = poller.result()
                
                # ページ内容を抽出
                page_content = ""
                if hasattr(result, 'content') and result.content:
                    page_content = result.content.strip()
                elif hasattr(result, 'pages') and result.pages:
                    # fallback: ページオブジェクトから抽出
                    for page in result.pages:
                        if hasattr(page, 'lines') and page.lines:
                            for line in page.lines:
                                if hasattr(line, 'content'):
                                    page_content += line.content + "\n"
                    page_content = page_content.strip()
                
                # ページにコンテンツがある場合のみ追加
                if page_content:
                    pages_content.append({
                        "page_number": page_number,
                        "content": page_content,
                        "source_file": file_name,
                        "page_file_name": page_file_name
                    })
                    print(f"ページ {page_number} の処理が完了しました ({len(page_content)} 文字)")
                else:
                    print(f"ページ {page_number} にコンテンツがありませんでした")
                    
            except Exception as e:
                print(f"ページ {page_number} の処理中にエラーが発生しました: {e}")
                continue
        
        print(f"合計 {len(pages_content)} ページの処理が完了しました")
        
        # 結果をキャッシュに保存
        if self.cache:
            self.cache.save_cache(file_bytes, file_name, pages_content)
        
        return pages_content
    
    def analyze_pdf_pages_with_enhanced_cache(self, file_bytes: bytes, file_name: str) -> List[Dict[str, Any]]:
        """
        強化キャッシュシステムを使用してPDFをページごとに分析（コスト最適化版）
        
        Args:
            file_bytes: PDFファイルのバイトデータ
            file_name: ファイル名（参照用）
            
        Returns:
            List[Dict]: ページごとのコンテンツとメタデータ
        """
        if not self.cache or self.cache_type != "enhanced":
            # 強化キャッシュが利用できない場合は通常処理
            return self.analyze_pdf_pages(file_bytes, file_name)
        
        from app.services.knowledge.utils.pdf_page_splitter import PDFPageSplitter
        import time
        
        print(f"💎 強化キャッシュシステムでPDF処理開始: {file_name}")
        
        # まず全文書レベルのキャッシュをチェック
        full_doc_cached_result = self.cache.get_full_document_cache(file_bytes, file_name)
        if full_doc_cached_result is not None:
            print(f"🎯 全文書キャッシュヒット: {file_name}")
            return full_doc_cached_result
        
        # 全文書キャッシュがない場合、ページ分割して個別キャッシュをチェック
        splitter = PDFPageSplitter()
        pdf_info = splitter.get_pdf_info(file_bytes)
        print(f"PDF情報: {pdf_info['page_count']} ページ - {file_name}")
        
        # PDFを個別ページに分割
        pages_data = splitter.split_pdf_to_pages(file_bytes, file_name)
        parent_hash = self.cache._get_file_hash(file_bytes)
        
        # 各ページを処理（キャッシュチェック + 必要に応じてAPI呼び出し）
        pages_content = []
        total_processing_time = 0.0
        
        for page_data in pages_data:
            page_number = page_data["page_number"]
            page_bytes = page_data["page_bytes"]
            page_file_name = page_data["page_file_name"]
            
            start_time = time.time()
            
            # 個別ページキャッシュをチェック
            cached_page_content = self.cache.get_page_cache(
                page_bytes, file_name, page_number, parent_hash
            )
            
            if cached_page_content is not None:
                # キャッシュヒット
                pages_content.append(cached_page_content)
                continue
            
            # キャッシュミス: Document Intelligence API呼び出し
            print(f"🔄 ページ {page_number} を Document Intelligence で処理中...")
            
            try:
                # Document Intelligence で処理
                poller = self.client.begin_analyze_document(
                    model_id="prebuilt-read",
                    body=page_bytes,
                    output_content_format="markdown",
                )
                result = poller.result()
                
                # ページ内容を抽出
                page_content = ""
                if hasattr(result, 'content') and result.content:
                    page_content = result.content.strip()
                elif hasattr(result, 'pages') and result.pages:
                    for page in result.pages:
                        if hasattr(page, 'lines') and page.lines:
                            for line in page.lines:
                                if hasattr(line, 'content'):
                                    page_content += line.content + "\n"
                    page_content = page_content.strip()
                
                processing_time = time.time() - start_time
                total_processing_time += processing_time
                
                if page_content:
                    page_result = {
                        "page_number": page_number,
                        "content": page_content,
                        "source_file": file_name,
                        "page_file_name": page_file_name
                    }
                    
                    pages_content.append(page_result)
                    
                    # 個別ページキャッシュに保存
                    self.cache.save_page_cache(
                        page_bytes, file_name, page_number, parent_hash,
                        page_result, processing_time
                    )
                    
                    print(f"✅ ページ {page_number} 処理完了 ({processing_time:.2f}秒)")
                else:
                    print(f"⚠️ ページ {page_number} にコンテンツがありませんでした")
                    
            except Exception as e:
                print(f"❌ ページ {page_number} の処理中にエラー: {e}")
                continue
        
        print(f"📊 処理完了: {len(pages_content)} ページ (総処理時間: {total_processing_time:.2f}秒)")
        
        # 全文書キャッシュとして保存（将来の高速化のため）
        if pages_content:
            self.cache.save_full_document_cache(
                file_bytes, file_name, pages_content, total_processing_time
            )
        
        return pages_content
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        キャッシュの統計情報を取得
        
        Returns:
            キャッシュの統計情報、キャッシュが無効の場合はNone
        """
        if self.cache:
            if self.cache_type == "enhanced":
                stats = self.cache.get_comprehensive_stats()
                stats["cache_type"] = "enhanced"
                return stats
            else:
                stats = self.cache.get_cache_stats()
                stats["cache_type"] = "legacy"
                return stats
        return {"cache_enabled": False, "cache_type": "disabled"}
    
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

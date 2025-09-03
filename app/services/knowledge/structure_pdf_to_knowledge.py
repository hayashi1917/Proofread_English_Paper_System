from libs.azure_client import AzureDocumentIntelligenceClient, AzureOpenAIClient
from langchain_core.prompts import ChatPromptTemplate
from app.schemas.schemas import KnowledgeFromLatexList, KnowledgeFromLatex
from app.services.knowledge.prompts.pdf_knowledge_extraction_prompts import SYSTEM_PROMPT, USER_PROMPT
from typing import List, Dict, Any


def structure_pdf_files_to_knowledge(pdf_files: List[Dict[str, Any]]) -> List[KnowledgeFromLatex]:
    """
    複数のPDFファイルからナレッジを抽出する
    
    Args:
        pdf_files: PDF ファイルの情報とバイトデータを含むリスト
        
    Returns:
        List[KnowledgeFromLatex]: 抽出されたナレッジのリスト
    """
    aggregated: List[KnowledgeFromLatex] = []
    azure_openai_client = AzureOpenAIClient()
    azure_doc_intel_client = AzureDocumentIntelligenceClient()
    
    for pdf_file in pdf_files:
        file_name = pdf_file["name"]
        file_bytes = pdf_file["content"]
        knowledge_type = pdf_file.get("knowledge_type", "一般的な論文")
        
        print(f"処理中のファイル: {file_name}")
        
        try:
            # Document Intelligenceでページごとの内容を抽出
            pages_content = azure_doc_intel_client.analyze_pdf_pages(file_bytes, file_name)
            
            print(f"PDFから{len(pages_content)}ページの内容を抽出しました")
            
            # 各ページからナレッジを抽出
            for page_data in pages_content:
                page_number = page_data["page_number"]
                page_content = page_data["content"]
                source_file = page_data["source_file"]
                
                print(f"ページ {page_number} を処理中...")
                print("--------------------------------")
                print("page_content:")
                print(page_content)
                print("--------------------------------")
                
                # プロンプトを作成してLLMでナレッジを抽出
                prompt = ChatPromptTemplate.from_messages([
                    ("system", SYSTEM_PROMPT),
                    ("user", USER_PROMPT),
                ])
                chain = prompt | azure_openai_client.get_openai_client().with_structured_output(KnowledgeFromLatexList)
                
                try:
                    results = chain.invoke({"content": page_content})
                    
                    # 抽出したナレッジにメタデータを追加
                    for result in results.knowledge_list:
                        result.knowledge_type = knowledge_type.strip() if knowledge_type else None
                        result.reference_url = f"{source_file} (Page {page_number})"
                        print("--------------------------------")
                        print("result:")
                        print(result)
                        print("--------------------------------")
                        aggregated.append(result)
                        
                except Exception as e:
                    print(f"ページ {page_number} の処理中にエラーが発生しました: {e}")
                    continue
                    
        except Exception as e:
            print(f"ファイル {file_name} の処理中にエラーが発生しました: {e}")
            continue
    
    print(f"合計 {len(aggregated)} 個のナレッジを抽出しました")
    return aggregated





def structure_pdf_files_to_knowledge_with_enhanced_cache(pdf_files: List[Dict[str, Any]]) -> List[KnowledgeFromLatex]:
    """
    強化キャッシュシステムを使用してPDFファイルからナレッジを抽出（コスト最適化版）
    
    Args:
        pdf_files: PDF ファイルの情報とバイトデータを含むリスト
        
    Returns:
        List[KnowledgeFromLatex]: 抽出されたナレッジのリスト
    """
    aggregated: List[KnowledgeFromLatex] = []
    azure_openai_client = AzureOpenAIClient()
    azure_doc_intel_client = AzureDocumentIntelligenceClient(enable_cache=True, use_enhanced_cache=True)
    
    print(f"💎 強化キャッシュシステムでPDF処理開始: {len(pdf_files)} ファイル")
    
    for pdf_file in pdf_files:
        file_name = pdf_file["name"]
        file_bytes = pdf_file["content"]
        knowledge_type = pdf_file.get("knowledge_type", "一般的な論文")
        
        print(f"処理中のファイル: {file_name}")
        
        try:
            # 強化キャッシュシステムでページ処理
            pages_content = azure_doc_intel_client.analyze_pdf_pages_with_enhanced_cache(file_bytes, file_name)
            
            print(f"PDFから{len(pages_content)}ページの内容を抽出しました")
            
            # 各ページからナレッジを抽出
            for page_data in pages_content:
                page_number = page_data["page_number"]
                page_content = page_data["content"]
                source_file = page_data["source_file"]
                
                print(f"ページ {page_number} からナレッジ抽出中...")
                print("--------------------------------")
                print("page_content:")
                print(page_content)
                print("--------------------------------")
                
                # プロンプトを作成してLLMでナレッジを抽出
                prompt = ChatPromptTemplate.from_messages([
                    ("system", SYSTEM_PROMPT),
                    ("user", USER_PROMPT),
                ])
                chain = prompt | azure_openai_client.get_openai_client().with_structured_output(KnowledgeFromLatexList)
                
                try:
                    results = chain.invoke({"content": page_content})
                    
                    # 抽出したナレッジにメタデータを追加
                    for result in results.knowledge_list:
                        result.knowledge_type = knowledge_type.strip() if knowledge_type else None
                        result.reference_url = f"{source_file} (Page {page_number})"
                        print("--------------------------------")
                        print("result:")
                        print(result)
                        print("--------------------------------")
                        aggregated.append(result)
                        
                except Exception as e:
                    print(f"ページ {page_number} のナレッジ抽出中にエラーが発生しました: {e}")
                    continue
                    
        except Exception as e:
            print(f"ファイル {file_name} の処理中にエラーが発生しました: {e}")
            continue
    
    # キャッシュ統計を表示
    cache_stats = azure_doc_intel_client.get_cache_stats()
    if "session" in cache_stats:
        session_stats = cache_stats["session"]
        from app.services.shared.logging_utils import log_proofreading_info
        log_proofreading_info(f"[structure_pdf_files_to_knowledge_with_enhanced_cache] セッション統計:")
        log_proofreading_info(f"[structure_pdf_files_to_knowledge_with_enhanced_cache]   キャッシュヒット: {session_stats['cache_hits']}")
        log_proofreading_info(f"[structure_pdf_files_to_knowledge_with_enhanced_cache]   キャッシュミス: {session_stats['cache_misses']}")
        log_proofreading_info(f"[structure_pdf_files_to_knowledge_with_enhanced_cache]   節約されたAPI呼び出し: {session_stats['api_calls_saved']}")
    
    from app.services.shared.logging_utils import log_proofreading_info
    log_proofreading_info(f"[structure_pdf_files_to_knowledge_with_enhanced_cache] 強化キャッシュシステムでの処理完了: 合計 {len(aggregated)} 個のナレッジを抽出しました")
    return aggregated
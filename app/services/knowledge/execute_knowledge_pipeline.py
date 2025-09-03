from app.schemas.schemas import KnowledgeFromLatexList, KnowledgeFromLatex
from app.services.knowledge.access_google_drive import download_knowledge_tex_files, download_knowledge_pdf_files
from app.services.knowledge.chunking_file import chunking_tex_files
from app.services.knowledge.structure_tex_to_knowledge import structure_tex_to_knowledge
from app.services.knowledge.structure_pdf_to_knowledge import structure_pdf_files_to_knowledge, structure_pdf_files_to_knowledge_with_enhanced_cache
from app.services.knowledge.utils.vector_store_service import VectorStoreService
from pathlib import Path
from dotenv import load_dotenv
import csv
from datetime import datetime
from typing import List
import pandas as pd
import ast
import os

load_dotenv(".env.local")

def save_knowledge_to_csv(knowledge_list: List[KnowledgeFromLatex], output_dir: str = "output") -> str:
    """
    KnowledgeFromLatexListをCSVファイルとして保存する
    
    Args:
        knowledge_list (KnowledgeFromLatexList): 保存するナレッジリスト
        output_dir (str): 出力ディレクトリのパス
        
    Returns:
        str: 保存したCSVファイルのパス
    """
    # 出力ディレクトリが存在しない場合は作成
    os.makedirs(output_dir, exist_ok=True)
    
    # ファイル名にタイムスタンプを含める
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"knowledge_{timestamp}.csv")
    
    # CSVファイルに書き込み
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['knowledge', 'issue_category', 'reference_url', 'knowledge_type'])
        writer.writeheader()
        
        for knowledge in knowledge_list:
            writer.writerow({
                'knowledge': knowledge.knowledge,
                'issue_category': knowledge.issue_category,
                'reference_url': knowledge.reference_url or '',
                'knowledge_type': knowledge.knowledge_type or ''
            })
    
    return output_path

def execute_knowledge_pipeline_batch() -> KnowledgeFromLatexList:
    # GoogleDriveからファイルを取得
    print("ファイルをGoogleドライブから取得中")
    tex_files = download_knowledge_tex_files(folder_id=os.getenv('TEST_FOLDER_ID'))
    # ファイルをチャンク分割
    print("ファイルをチャンク分割中")
    chunks = chunking_tex_files(tex_files)
    # チャンク分割したファイルからナレッジのリストを作成
    print("ナレッジのリストを作成中")
    knowledge_list = structure_tex_to_knowledge(chunks)
    
    # CSVファイルとして保存
    print("CSVファイルとして保存中")
    output_path = save_knowledge_to_csv(knowledge_list)

    print(f"Knowledge saved to: {output_path}")

    return knowledge_list


def execute_knowledge_pipeline_from_pdf_batch(pdf_folder_id: str = None, use_page_splitting: bool = True, use_enhanced_cache: bool = True) -> List[KnowledgeFromLatex]:
    """
    Google DriveからPDFファイルを取得してナレッジを抽出するパイプライン
    
    Args:
        pdf_folder_id: Google DriveのPDFフォルダID（未指定の場合は環境変数を使用）
        use_page_splitting: True の場合はページ分割処理を使用、False の場合は従来の処理
        use_enhanced_cache: True の場合は強化キャッシュシステムを使用
        
    Returns:
        List[KnowledgeFromLatex]: 抽出されたナレッジのリスト
    """
    from app.services.shared.logging_utils import log_proofreading_info, log_proofreading_debug
    
    # フォルダIDが指定されていない場合は環境変数を使用
    if pdf_folder_id is None:
        pdf_folder_id = os.getenv('TEST_FOLDER_ID')
    
    log_proofreading_info(f"[execute_knowledge_pipeline_from_pdf_batch] PDFナレッジパイプライン開始 - フォルダID: {pdf_folder_id}")
    log_proofreading_info(f"[execute_knowledge_pipeline_from_pdf_batch] 設定 - ページ分割: {use_page_splitting}, 強化キャッシュ: {use_enhanced_cache}")
    
    log_proofreading_info("[execute_knowledge_pipeline_from_pdf_batch] Google DriveからPDFファイル取得開始")
    pdf_files = download_knowledge_pdf_files(folder_id=pdf_folder_id)
    
    if not pdf_files:
        log_proofreading_info("[execute_knowledge_pipeline_from_pdf_batch] PDFファイルが見つかりませんでした")
        return []
    
    log_proofreading_info(f"[execute_knowledge_pipeline_from_pdf_batch] 取得完了: {len(pdf_files)}個のPDFファイル")
    
    # ファイル一覧をログ出力
    for i, pdf_file in enumerate(pdf_files):
        log_proofreading_debug(f"[execute_knowledge_pipeline_from_pdf_batch] ファイル{i+1}: {pdf_file['name']} ({pdf_file['size']} bytes)")
    
    # PDFファイルからナレッジを抽出
    if use_enhanced_cache and use_page_splitting:
        log_proofreading_info("[execute_knowledge_pipeline_from_pdf_batch] ナレッジ抽出開始（強化キャッシュ + ページ分割処理）")
        knowledge_list = structure_pdf_files_to_knowledge_with_enhanced_cache(pdf_files)
    else:
        log_proofreading_info("[execute_knowledge_pipeline_from_pdf_batch] ナレッジ抽出開始（従来の処理）")
        knowledge_list = structure_pdf_files_to_knowledge(pdf_files)
    
    # CSVファイルとして保存
    log_proofreading_info("[execute_knowledge_pipeline_from_pdf_batch] ナレッジをCSVファイルとして保存中")
    output_path = save_knowledge_to_csv(knowledge_list)
    
    log_proofreading_info(f"[execute_knowledge_pipeline_from_pdf_batch] 処理完了 - 保存先: {output_path}")
    log_proofreading_info(f"[execute_knowledge_pipeline_from_pdf_batch] 抽出されたナレッジ数: {len(knowledge_list)}")
    
    return knowledge_list


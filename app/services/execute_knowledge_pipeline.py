from app.schemas.schemas import KnowledgeFromLatexList, KnowledgeFromLatex
from app.services.access_google_drive import download_knowledge_tex_files, download_knowledge_pdf_files
from app.services.chunking_file import chunking_tex_files
from app.services.structure_tex_to_knowledge import structure_tex_to_knowledge
from app.services.structure_pdf_to_knowledge import structure_pdf_files_to_knowledge
from app.services.utils.vector_store_service import VectorStoreService
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


def execute_knowledge_pipeline_from_pdf_batch(pdf_folder_id: str = None) -> List[KnowledgeFromLatex]:
    """
    Google DriveからPDFファイルを取得してナレッジを抽出するパイプライン
    
    Args:
        pdf_folder_id: Google DriveのPDFフォルダID（未指定の場合は環境変数を使用）
        
    Returns:
        List[KnowledgeFromLatex]: 抽出されたナレッジのリスト
    """
    # フォルダIDが指定されていない場合は環境変数を使用
    if pdf_folder_id is None:
        pdf_folder_id = os.getenv('TEST_FOLDER_ID')
    
    print("PDFファイルをGoogleドライブから取得中")
    pdf_files = download_knowledge_pdf_files(folder_id=pdf_folder_id)
    
    if not pdf_files:
        print("PDFファイルが見つかりませんでした")
        return []
    
    print(f"{len(pdf_files)}個のPDFファイルを取得しました")
    
    # PDFファイルからナレッジを抽出
    print("PDFファイルからナレッジを抽出中")
    knowledge_list = structure_pdf_files_to_knowledge(pdf_files)
    
    # CSVファイルとして保存
    print("CSVファイルとして保存中")
    output_path = save_knowledge_to_csv(knowledge_list)
    
    print(f"PDF Knowledge saved to: {output_path}")
    print(f"抽出されたナレッジ数: {len(knowledge_list)}")
    
    return knowledge_list


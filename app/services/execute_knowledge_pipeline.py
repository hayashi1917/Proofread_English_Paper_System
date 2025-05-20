from app.schemas.schemas import KnowledgeFromLatexList, KnowledgeFromLatex
from app.services.access_google_drive import download_knowledge_tex_files
from app.services.chunking_file import chunking_tex_files
from app.services.structure_tex_to_knowledge import structure_tex_to_knowledge
import os
from dotenv import load_dotenv
import csv
from datetime import datetime
from typing import List

load_dotenv(".env.local")

def save_knowledge_to_csv(knowledge_list: KnowledgeFromLatexList, output_dir: str = "output") -> str:
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
        
        for knowledge in knowledge_list.knowledge_list:
            writer.writerow({
                'knowledge': knowledge.knowledge,
                'issue_category': knowledge.issue_category,
                'reference_url': knowledge.reference_url or '',
                'knowledge_type': knowledge.knowledge_type or ''
            })
    
    return output_path

def execute_knowledge_pipeline_batch() -> KnowledgeFromLatexList:
    # GoogleDriveからファイルを取得
    tex_files = download_knowledge_tex_files(folder_id=os.getenv('KNOWLEDGE_TEX_FOLDER_ID'))
    # ファイルをチャンク分割
    chunks = chunking_tex_files(tex_files)
    # チャンク分割したファイルからナレッジのリストを作成
    knowledge_list = structure_tex_to_knowledge(chunks)
    
    # CSVファイルとして保存
    output_path = save_knowledge_to_csv(knowledge_list)
    print(f"Knowledge saved to: {output_path}")

    return knowledge_list

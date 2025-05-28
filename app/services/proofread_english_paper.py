from app.services.access_google_drive import download_pre_proofread_tex_file
from app.services.chunking_file import chunking_tex_file
from app.services.create_queries_by_HyDE import create_queries_by_HyDE
from app.services.proofread_paper_by_knowledge import proofread_paper_by_knowledge
from dotenv import load_dotenv
import os
from typing import List, Dict


load_dotenv(".env.local")

def proofread_english_paper() -> List[Dict[str, str]]:

    folder_id = os.getenv("ENGLISH_PAPER_BEFORE_PROOFREADING_FOLDER_ID")
    # 校正前論文を取得 None -> LaTeX: str
    tex_file = download_pre_proofread_tex_file(folder_id=folder_id)

    # LaTeXをセクションごとに分割　 LaTeX: str -> sections:List[Dict[str, str]]
    sections = chunking_tex_file(tex_file)

    # セクションごとに、HyDEをつかって検査クエリを生成　
    # 検査クエリを実行して、結果を取得
    # LLMと、検索結果を組み合わせて、校正結果を生成
    results = proofread_paper_by_knowledge(sections)

    return results

def proofread_english_paper_posted_file(tex_file: str) -> List[Dict[str, str]]:
    """
    アップロードされたファイルを校正する。
    
    Args:
        file (str): アップロードされたLaTeXファイルのパス
    
    Returns:
        List[Dict[str, str]]: 校正結果のリスト
    """
    # LaTeXをセクションごとに分割
    sections = chunking_tex_file(tex_file)

    # セクションごとに、HyDEをつかって検査クエリを生成
    results = proofread_paper_by_knowledge(sections)

    return results
from app.services.execute_knowledge_pipeline import KnowledgeFromLatex
from app.services.utils.vector_store_service import VectorStoreService
from pathlib import Path
import pandas as pd
import ast

def csv_to_db(csv_file_name: str):
    script_file_path = Path(__file__) # your_script.py のフルパス

    # 2. スクリプトファイルの親ディレクトリを取得
    script_dir = script_file_path.parent # your_script.py があるディレクトリ (例: .../app/services/)

    # 3. プロジェクトのルートディレクトリを基準にCSVファイルのパスを構築
    #    この例では、your_script.py から見て2つ上の階層がプロジェクトルートだと仮定
    project_root_dir = script_dir.parent.parent
    csv_path = project_root_dir / 'output' / csv_file_name
    df = pd.read_csv(csv_path)
    print(df)
    knowledge_list = []
    for index, row in df.iterrows():
        issue_category = ast.literal_eval(row['issue_category'])
        knowledge_list.append(KnowledgeFromLatex(knowledge=row['knowledge'], issue_category=issue_category, reference_url=row['reference_url'], knowledge_type=row['knowledge_type']))
    # ベクトルスDBに保存
    print("ベクトルDBに保存中")
    vector_store_service = VectorStoreService()
    vector_store_service.add_knowledge_to_vector_store(knowledge_list)

    return {"message": "ベクトルDBに保存しました"}
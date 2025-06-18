import json
from datetime import datetime
import os

def save_output_file(dict: dict) -> None:
    # 結果をJSONファイルとして保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"analysis_result_{timestamp}.json"
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, filename), "w") as f:
        json.dump(dict, f)
from libs.azure_client import AzureDocumentIntelligenceClient, AzureOpenAIClient
from langchain_core.prompts import ChatPromptTemplate
from app.schemas.schemas import KnowledgeFromLatexList, KnowledgeFromLatex
import typing
from typing import List, Dict, Any
import json

SYSTEM_PROMPT = """
あなたは学術ドキュメントのフォーマットと英文校正に関する専門家です。
あなたの主な目的は、入力されたPDFページから、論文執筆者が論文の**内容や体裁の質（＝校正）を向上させ、学会フォーマットに適合させるために直接的に行動に移せる、具体的かつ実行可能な指示・ルール・仕様のみ**を「ナレッジ単位」で抽出し、JSON 配列として出力することです。
各ナレッジは、それ単体で意味が通じるように、具体的で簡潔な体言止めで記述してください。
"""

USER_PROMPT = """
# ナレッジの定義と抽出基準
- **抽出対象 (校正に関連するナレッジとするもの)**:
    - 論文の見た目、読みやすさ、構成、文法、単語選択、記号の使い方など、論文の質に直接関わる具体的なフォーマット指示 (例: 「フォントサイズは10ポイントに設定」「タイトルは米国の大文字ルールに従うこと」)
    - 明確な禁止事項（校正および体裁に関するもの） (例: 「タイプ3フォントの使用禁止」)
    - 実行可能な推奨事項（校正および体裁に関するもの） (例: 「図の環境でのセンタリング推奨」)
    - 論文構成に関する具体的なルール（内容の質や読みやすさに関わるもの） (例: 「要約は200語以内に制限」「ページ番号は印刷しない」)
    - 参考文献や引用の具体的なスタイル指示 (例: 「引用は著者名と年を記載」)
    - 図表のキャプション、解像度、配置など、論文内での見た目や内容の表現に関する指示 (例: 「図のキャプションは図の下に配置」)

- **抽出対象外 (校正に関係ない、またはナレッジではないもの)**:
    - **提出手続きやファイル管理に関する指示**: (例: 「PDFファイルを提出すること」「単一の.texファイルとしてLaTeXソースを提出すること」「ファイル名は姓で命名すること」「ソースファイルを圧縮して提出」)
    - **出版の可否条件や事務的なプロセス、著者登録に関する情報**: (例: 「署名された著作権フォームがない場合、論文は出版されない」「論文提出は二段階のプロセスであること」「著者登録と提出手順を確認すること」)
    - 背景情報、単なる理由説明 (例: 「均一な外観のため指示に従う必要性」)
    - 他の情報源へのポインタや参照指示 (例: 「詳細は別紙参照」)
    - 手続きの概要説明、一般的なアドバイス (例: 「問題があればソースファイルを修正」)
    - 免責事項、著作権者、謝辞、挨拶、テンプレートの作者や貢献者に関する情報
    - 具体的な対象（例: 「特定のコマンド」）や方法（例: 「適切な設定」）が記述されていない曖昧な指示や、抽象的な目標 (例: 「論文はシンプルに保つこと」「文書の内容が明確であることを確認」)
    - LaTeXの一般的な説明や、ソフトウェアの操作方法そのもの
    - テンプレートのバージョン情報や更新履歴


# 制約
* 上記「ナレッジの定義と抽出基準」を厳密に遵守し、**特に「抽出対象外」に該当する情報は絶対に含めない**こと。
* 抽出するナレッジは、論文の**英文校正および内容・体裁のフォーマット適合に直接役立つ具体的な指示・ルールのみ**とする。
* JSON 形式の配列以外は絶対に出力しない (説明文、前置き、後書き、```json ```のようなマークダウン装飾も一切不要)。
* LaTeX コマンドや数式は、その指示内容が論文の体裁や内容にどう影響するかを日本語で平易に表現するか、指示内容に直接関わらない場合は除去する。
* 内容が実質的に同一のナレッジは重複して抽出しない。意味や指示内容が同じであれば、表現が多少異なっていても重複とみなす。

# 入力資料（PDFページ内容）
{content}
"""


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


def structure_pdf_to_knowledge_from_chunks(chunks: List[Dict[str, Any]]) -> List[KnowledgeFromLatex]:
    """
    チャンク化されたPDFデータからナレッジを抽出する（既存のパイプラインとの互換性のため）
    
    Args:
        chunks: チャンク化されたドキュメントデータ
        
    Returns:
        List[KnowledgeFromLatex]: 抽出されたナレッジのリスト
    """
    aggregated: List[KnowledgeFromLatex] = []
    azure_openai_client = AzureOpenAIClient()
    
    for document in chunks:
        document_name = document["name"]
        knowledge_type = document.get("knowledge_type", "PDF")
        
        for chunk in document["chunks"]:
            chunk_text = chunk["chunk_text"]
            print("--------------------------------")
            print("chunk_text:")
            print(chunk_text)
            print("--------------------------------")
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", SYSTEM_PROMPT),
                ("user", USER_PROMPT),
            ])
            chain = prompt | azure_openai_client.get_openai_client().with_structured_output(KnowledgeFromLatexList)
            
            try:
                results = chain.invoke({"content": chunk_text})
                
                for result in results.knowledge_list:
                    result.knowledge_type = knowledge_type.strip() if knowledge_type else None
                    result.reference_url = document_name
                    print("--------------------------------")
                    print("result:")
                    print(result)
                    print("--------------------------------")
                    aggregated.append(result)
                    
            except Exception as e:
                print(f"チャンク処理中にエラーが発生しました: {e}")
                continue
    
    return aggregated
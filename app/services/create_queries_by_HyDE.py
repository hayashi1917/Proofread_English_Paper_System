from libs.azure_client import AzureOpenAIClient
from typing import List, Dict, Any
from langchain.prompts import ChatPromptTemplate
from app.schemas.schemas import CreateQueriesByHyDE
SYSTEM_PROMPT = """
あなたは英語学術論文の校正を専門とする言語学エキスパートです。

## 使命：HyDE手法による校正クエリ生成
与えられたLaTeXセクションを分析し、英語論文として改善が必要な項目を特定し、
その項目に関連する校正知識を検索するための具体的クエリを生成してください。

## 専門領域
- 学術英語の文法・語法体系
- 論文特有の修辞技法と表現パターン  
- 学術文書の構造・形式規範
- 分野別専門用語の適切な使用

## HyDEアプローチ
Hypothetical Document Embeddings手法で、以下の手順でクエリを生成：
1. セクション内の潜在的問題を仮定
2. 問題解決に必要な理想的な校正知識を想定
3. その知識を検索するための具体的キーワードを生成
"""

USER_PROMPT ="""
# HyDEクエリ生成タスク
以下のLaTeXセクションを分析し、英語学術論文としての改善項目を特定してください。

## 分析観点
### 1. 文法・語法項目
- 時制使用（現在完了、過去形、受動態等）
- 冠詞の適切性（a/an/theの使い分け）
- 前置詞の選択と使用法
- 主述一致、代名詞の照合
- 語順と文構造

### 2. 語彙・表現項目  
- 学術的語彙の選択
- 専門用語の統一性
- 客観的表現への訂正
- 簡潔性と明確性の向上

### 3. 構造・形式項目
- 段落構成と論理的流れ
- 接続語句の適切な使用
- 引用形式と参考文献表記
- 図表参照とキャプション
- 数式表記と記号使用

### 4. 専門性・一貫性項目
- 略語の定義と使用
- 技術用語の正確性
- 単位と数値の表記
- フォントとスタイル統一

## 出力要求
上記観点で分析し、実際に改善が必要な項目を具体的なキーワード・フレーズで出力してください。

**出力例:**
- "現在完了時制"
- "定冠詞の欠落"
- "受動態の適切性"
- "専門用語の統一"
- "図表参照の正確性"
- "接続語句の選択"

## 対象セクション
{section_content}

上記テキストから、実際に校正が必要な具体的項目のみを抽出し、
知識ベース検索用のクエリとして出力してください。
"""



def create_queries_by_HyDE(section: str) -> List[str]:
    """
    HyDE（Hypothetical Document Embeddings）手法を使用した英語論文校正クエリ生成。
    
    与えられたLaTeXセクションを分析し、潜在的な文法・語法・表現・構造上の
    問題を特定し、その問題解決に必要な校正知識を検索するための
    具体的なクエリを生成する。

    HyDEプロセス:
    1. セクション内容の言語学的分析
    2. 潜在的文法・語法問題の仮定
    3. 問題解決に必要な理想的校正知識の想定
    4. 知識ベース検索用クエリの具体化

    Parameters
    ----------
    section : str
        校正対象のLaTeXセクションテキスト

    Returns
    -------
    List[str]
        英語論文校正用の具体的検索クエリリスト
        （文法項目、表現技法、専門用語、構造上の改善点等）
    """
    # === HyDE (Hypothetical Document Embeddings) 実行 ===
    # 1. セクション内容を言語学的に分析し、潜在的な文法・語法問題を特定
    # 2. 問題解決に必要な理想的な校正知識を仮定
    # 3. その知識を検索するための具体的なクエリキーワードを生成
    # 4. 生成されたクエリで知識ベースを検索し、関連する校正知識を取得

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("user", USER_PROMPT),
    ])
    chain = prompt | AzureOpenAIClient().get_openai_client().with_structured_output(CreateQueriesByHyDE)
    result = chain.invoke({"section_content": section})
    queries: List[str] = result.queries

    return queries

def create_queries_by_HyDE_from_sections(sections: str) -> List[Dict[str, List[str]]]:
    """
    セクションごとにHyDEを使用して検査クエリを生成する。

    Parameters
    ----------
    sections : List[Dict[str, str]]
        セクションのリスト。各セクションは辞書形式で、キーはセクション名、値はセクションの内容。

    Returns
    -------
    List[Dict[str, List[str]]]
        各セクションに対する検査クエリのリスト。各辞書はセクション名とその検査クエリのリストを含む。
    """
    queries = []
    for section in sections:
        section_content = section
        generated_queries = create_queries_by_HyDE(section_content)
        queries.append(generated_queries)
    
    return queries
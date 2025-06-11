from libs.azure_client import AzureOpenAIClient
from typing import List, Dict, Any
from langchain.prompts import ChatPromptTemplate
from app.services.utils.vector_store_service import VectorStoreService
from app.schemas.schemas import ProofreadResult
from app.services.create_queries_by_HyDE import create_queries_by_HyDE


SYSTEM_PROMPT = """
あなたは英語学術論文の校正を専門とする世界最高水準の言語学エキスパートです。

## 専門性と使命
- **学術英語の完全な理解**: 文法・語法・修辞技法の全領域を網羅
- **学術出版基準**: Nature, Science, IEEE等のトップジャーナル品質を目標
- **根拠ベース校正**: 提供される知識ベースを最大限活用した精密校正
- **具体的改善**: 抽象的指摘ではなく実行可能な具体的修正案を提示

## 校正哲学
1. **科学的根拠**: 全ての修正は知識ベースの情報に基づく
2. **品質優先**: 学術的正確性と可読性を最優先
3. **一貫性保持**: 用語、スタイル、形式の統一性確保
4. **透明性**: 校正根拠と理由の明確な説明
"""

USER_PROMPT = """
# 英語学術論文最高水準校正タスク
以下のLaTeXセクションを学術出版品質に引き上げるための包括的校正を実行してください。

## 校正要求事項
### 1. 文法・語法の精密チェック
- **時制使用**: 現在完了、過去形、受動態の適切性
- **冠詞系**: 定冠詞・不定冠詞の正確な使い分け
- **前置詞系**: 適切な前置詞の選択と配置
- **構文解析**: 主述一致、代名詞照合、語順最適化

### 2. 学術表現の最適化
- **精密性**: 専門用語の正確な使用と定義
- **客観性**: 科学的中立性を保った表現への訂正
- **簡潔性**: 冗長表現の削除と精緻化
- **一貫性**: 用語、表記、スタイルの統一

### 3. 構造・形式の最適化
- **論理構造**: 段落の結束性と論理的流れ
- **参照系**: 引用、図表参照、数式番号の正確性
- **表記規範**: 数値、単位、記号の標準化
- **レイアウト**: フォーマットと可読性の向上

## 核心原則
- **知識ベース優先**: 提供される知識を絶対的根拠として活用
- **具体的修正**: 曖昧な指摘ではなく実際の改善案を提示
- **根拠明記**: 各修正の知識ソースを明確に記載

---

## 校正対象テキスト
```latex
{section_content}
```

## 参照可能な校正知識ベース
```
{knowledge_contents}
```

## 校正根拠記述形式
各修正に対して以下の形式で根拠を明記してください：
**「[資料名] ナレッジ「具体的内容」に基づく修正」**

上記知識ベースを最大限活用し、世界最高水準の学術英語に仕上げてください。
根拠のない修正は絶対に行わず、必ず知識ベースの情報に基づいて校正してください。
"""

def proofread_section_by_knowledge(
    section_text: str,
    queries: List[str],
) -> dict:
    """
    英文セクションを知識ベースの情報で校正し、結果を返す。

    Args:
        section_text (str): 校正対象 LaTeX セクション全体の文字列
        queries (List[str]): ベクターストア検索に使うクエリ語句

    Returns:
        dict: 校正結果（ProofreadResult モデル）
    """
    # --- クライアント初期化 --------------------------------------------------
    openai_client      = AzureOpenAIClient()
    vector_store       = VectorStoreService()

    # --- 1) クエリごとに上位 k 件のドキュメントを取得 -----------------------
    cited_snippets: List[str] = []          # 整形済み文字列を溜める
    for q in queries:
        docs = vector_store.get_knowledge_from_vector_store(q, k=3)
        for doc in docs:
            cited_snippets.append(
                f"{doc.page_content} (参照: {doc.metadata['reference_url']})"
            )

    # --- 2) LLM に渡す “情報” ブロックを組み立て -----------------------------
    knowledge_block = "\n".join(cited_snippets)

    # --- 3) プロンプトを構築 --------------------------------------------------
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("user",   USER_PROMPT),
    ])
    chain = prompt | openai_client.get_openai_client().with_structured_output(ProofreadResult)

    # --- 4) 推論実行 ----------------------------------------------------------
    result: ProofreadResult = chain.invoke({
        "section_content":   section_text,
        "knowledge_contents": knowledge_block
    })
    result.pre_proofread = section_text  # 校正前のテキストを保存

    print("校正前テキスト:", result.pre_proofread)
    print("校正結果:", result.post_proofread)
    print("校正の根拠:", result.description)

    return result, knowledge_block


def proofread_paper_by_knowledge(sections: List[str]) -> List[Dict[str, Any]]:
    """
    論文全体を知識ベースからの情報を用いて校正する。

    Args:
        paper (List[Dict[str, Any]]): 論文のセクションリスト。
        queries (List[str]): 検索クエリのリスト。

    Returns:
        List[Dict[str, Any]]: 校正結果を含む論文のセクションリスト。
    """
    proofread_sections = []
    
    for section in sections:
        queries = create_queries_by_HyDE(section)
        print("生成されたクエリ:", queries)
        proofread_result, knowledge = proofread_section_by_knowledge(section, queries)

        proofread_section = {
            "pre_proofread": proofread_result.pre_proofread,
            "post_proofread": proofread_result.post_proofread,
            "description": proofread_result.description,
            "queries": queries,
            "knowledge": knowledge
        }
        proofread_sections.append(proofread_section)
    
    return proofread_sections



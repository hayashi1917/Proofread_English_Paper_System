from libs.azure_client import AzureOpenAIClient
from typing import List, Dict, Any
from langchain.prompts import ChatPromptTemplate
from app.services.utils.vector_store_service import VectorStoreService
from app.schemas.schemas import ProofreadResult
from app.services.create_queries_by_HyDE import create_queries_by_HyDE


SYSTEM_PROMPT = """あなたは、英語論文を校正するエキスパートです。
以下に与えられる指示と出力形式を厳守し、与えられたセクションの内容を検査し、誤りを指摘してください。"""

USER_PROMPT = """
# 指示
与えられるLaTeXのセクションから、どの項目が誤りで修正すべきかを示し、正しく修正してください。
以下に、校正に役立つ知識を提供するので、そこで指摘されていることを忠実に守り、修正を行ってください。
校正の根拠は、どの資料のナレッジを参考にし構成したかを、例に従って記述してください。

# 校正根拠の詣式
校正根拠の例：資料〇〇のナレッジ「◻︎◻︎」を参照

# 校正前テキスト
{section_content}

# 情報
{knowledge_contents}


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



from libs.azure_client import AzureOpenAIClient
from typing import List, Dict, Any
from langchain.prompts import ChatPromptTemplate
from app.schemas.schemas import CreateQueriesByHyDE
SYSTEM_PROMPT = """
あなたは、英語論文を校正するエキスパートです。
以下に与えられる指示と出力形式を厳守し、与えられたセクションの内容を検査し、誤りを指摘してください。
"""

USER_PROMPT ="""
# 指示
与えられるLaTeXのセクションから、どの項目が誤りで修正すべきかを示してください。
修正する項目がどのようなものであるかを、単語やフレーズで出力してください。

# 出力の例
図表、グラフ、冠詞、過去形、...

# セクションの内容
{section_content}
"""



def create_queries_by_HyDE(section: str) -> List[str]:
    """
    HyDEを使用して、与えられたセクションから検査クエリを生成する。

    Parameters
    ----------
    section : str
        セクションのテキスト

    Returns
    -------
    List[str]
        生成された検査クエリのリスト
    """
    # HyDEのロジックをここに実装
    # 例として、セクションの内容からキーワードを抽出してクエリを生成する

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
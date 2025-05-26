from typing import Optional, Literal, List
from pydantic import BaseModel, Field, constr, conlist

class AnalyzeDocumentResponse_PrebuiltLayout(BaseModel):
    content: str
    tables: list[dict]
    key_value_pairs: list[dict]
    entities: list[dict]
    
class StructureResultResponse(BaseModel):
    markdown: str = Field(description="Markdown形式のテキスト")

class KnowledgeFromLatex(BaseModel):
    knowledge: str = Field(..., description="ナレッジのテキスト")

    issue_category: conlist(
        Literal["段落構成", "文法", "単語", "形式"], min_length=1, max_length=2) = Field(..., description="問題カテゴリ")

    reference_url: Optional[str] = Field(description="参考URL／ファイルパスなど")
    knowledge_type: Optional[Literal["学会フォーマット", "一般的な論文", "論文指導"]] = Field(description="ナレッジのタイプ")


class KnowledgeFromLatexList(BaseModel):
    knowledge_list: conlist(KnowledgeFromLatex, min_length=1, max_length=10) = Field(..., description="ナレッジのリスト（1〜10 件）")

class SearchKnowledgeQuery(BaseModel):
    query: str = Field(..., description="検索クエリ")

class CreateQueriesByHyDE(BaseModel):
    queries : conlist(str, min_length=1, max_length=10) = Field(
        ...,
        description="HyDEによる生成クエリのリスト（1〜10 件）"
    )

class ProofreadResult(BaseModel):
    pre_proofread: Optional[str] = Field(
        None, 
        description="校正前のテキスト"
    )
    post_proofread: str = Field(
        ..., 
        description="校正後のテキスト"
    )
    description: str = Field(
        ..., 
        description="校正の根拠"
    )


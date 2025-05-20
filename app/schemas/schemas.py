from pydantic import BaseModel, Field
from typing import Optional
class AnalyzeDocumentResponse_PrebuiltLayout(BaseModel):
    content: str
    tables: list[dict]
    key_value_pairs: list[dict]
    entities: list[dict]
    
class StructureResultResponse(BaseModel):
    markdown: str = Field(description="Markdown形式のテキスト")

class KnowledgeFromLatex(BaseModel):
    knowledge: str = Field(description="ナレッジのテキスト")
    issue_category: str = Field(description="問題のカテゴリ. [段落構成 | 文法 | 単語 | 形式] から 1–2 個")
    reference_url: Optional[str] = Field(description="参考URL, ナレッジの出典")
    knowledge_type: Optional[str] = Field(description="ナレッジのタイプ. 学会フォーマット | 一般的な論文 | 論文指導")


class KnowledgeFromLatexList(BaseModel):
    knowledge_list: list[KnowledgeFromLatex] = Field(description="ナレッジのリスト")
    
from pydantic import BaseModel, Field

class AnalyzeDocumentResponse_PrebuiltLayout(BaseModel):
    content: str
    tables: list[dict]
    key_value_pairs: list[dict]
    entities: list[dict]
    
class StructureResultResponse(BaseModel):
    markdown: str = Field(description="Markdown形式のテキスト")
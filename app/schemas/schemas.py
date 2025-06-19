from typing import Optional, Literal, List
from pydantic import BaseModel, Field, constr, conlist, field_validator
from enum import Enum

class AnalyzeDocumentResponse_PrebuiltLayout(BaseModel):
    content: str
    tables: list[dict]
    key_value_pairs: list[dict]
    entities: list[dict]
    
class StructureResultResponse(BaseModel):
    markdown: str = Field(description="Markdown形式のテキスト")

class KnowledgeFromLatex(BaseModel):
    knowledge: str = Field(..., description="ナレッジのテキスト（背景、使われるべき状況、例を含む詳細な形式）")

    issue_category: conlist(
        Literal["段落構成", "文法", "単語", "形式"], min_length=1, max_length=2) = Field(..., description="問題カテゴリ")

    reference_url: Optional[str] = Field(description="参考URL／ファイルパスなど")
    knowledge_type: Optional[Literal["学会フォーマット", "一般的な論文", "論文指導", "PDF文書"]] = Field(description="ナレッジのタイプ")
    
    @field_validator('knowledge_type')
    @classmethod
    def normalize_knowledge_type(cls, v):
        if v is not None:
            # 前後の空白文字（全角・半角）を除去
            return v.strip().strip('\u3000')
        return v


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
    sentences: List[str] = Field(
        ..., 
        description="校正箇所の英文"
    )


# 分割テスト用スキーマ
class SplitModeEnum(str, Enum):
    SECTION = "section"
    COMMAND = "command" 
    SENTENCE = "sentence"
    HYBRID = "hybrid"
    RECURSIVE_NLP = "recursive_nlp"


class LaTeXSplitRequest(BaseModel):
    latex_content: str = Field(
        ..., 
        description="分割対象のLaTeXコンテンツ",
        min_length=10,
        max_length=100000
    )
    split_mode: SplitModeEnum = Field(
        SplitModeEnum.SECTION,
        description="分割モード"
    )


class ChunkInfo(BaseModel):
    chunk_id: int = Field(..., description="チャンクID")
    content: str = Field(..., description="チャンクの内容")
    length: int = Field(..., description="チャンクの文字数")
    chunk_type: Optional[str] = Field(None, description="チャンクのタイプ（プリアンブル、本文など）")


class LaTeXSplitResponse(BaseModel):
    split_mode: SplitModeEnum = Field(..., description="使用した分割モード")
    total_chunks: int = Field(..., description="総チャンク数")
    original_length: int = Field(..., description="元のテキストの文字数")
    chunks: List[ChunkInfo] = Field(..., description="分割されたチャンクのリスト")
    processing_time_ms: float = Field(..., description="処理時間（ミリ秒）")


class MultipleSplitRequest(BaseModel):
    latex_content: str = Field(
        ..., 
        description="分割対象のLaTeXコンテンツ",
        min_length=10,
        max_length=100000
    )
    split_modes: List[SplitModeEnum] = Field(
        [SplitModeEnum.SECTION, SplitModeEnum.SENTENCE, SplitModeEnum.HYBRID],
        description="比較する分割モードのリスト"
    )


class SplitComparison(BaseModel):
    split_mode: SplitModeEnum = Field(..., description="分割モード")
    chunk_count: int = Field(..., description="チャンク数")
    processing_time_ms: float = Field(..., description="処理時間（ミリ秒）")
    sample_chunks: List[str] = Field(..., description="サンプルチャンク（最初の3つ）")


class MultipleSplitResponse(BaseModel):
    original_length: int = Field(..., description="元のテキストの文字数")
    comparisons: List[SplitComparison] = Field(..., description="各分割モードの比較結果")
    recommended_mode: SplitModeEnum = Field(..., description="推奨分割モード")
    total_processing_time_ms: float = Field(..., description="全体処理時間（ミリ秒）")


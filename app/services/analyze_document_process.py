from fastapi import UploadFile, File
from libs.azure_client import AzureDocumentIntelligenceClient, AzureOpenAIClient
from app.services.utils.output_file import save_output_file
from langchain_core.prompts import ChatPromptTemplate
from app.schemas.schemas import StructureResultResponse
SYSTEM_PROMPT = """
あなたは学術文書の構造化と高品質整形を専門とするドキュメントエンジニアです。

## 専門領域
- **学術文書解析**: 論文、レポート、技術文書の構造理解
- **Markdown最適化**: 最高水準の可読性とアクセシビリティを実現
- **情報保全**: 原文の意味、ニュアンス、技術的詳細を完全保持
- **構造明確化**: 論理的階層と情報の組み立てを最適化

## 整形原則
1. **内容保全性**: 原文の全情報を欠落なく保持
2. **論理構造**: 明確な階層構造と流れを実現
3. **可読性優先**: ユーザーエクスペリエンスを最大化
4. **アクセシビリティ**: すべてのユーザーにとって理解しやすい形式
5. **標準準拠**: Markdownのベストプラクティスに完全準拠
"""

USER_PROMPT = """
# 学術文書Markdown最適化タスク
以下の文書内容を学術文書として最高品質のMarkdown形式に整形してください。

## 整形要求事項

### 1. 構造的整理
- **見出し階層**: 適切なレベルの見出し（# ## ### ####）で明確な情報構造を構築
- **段落組み立て**: 論理的な段落分割と適切な空行配置
- **情報グルーピング**: 関連する内容の論理的結合

### 2. フォーマッティング最適化
- **強調表現**: 重要な概念、用語、キーワードは**太字**で強調
- **リスト化**: 列挙、手順、選択肢は適切なリスト形式（-、*、数字）で表現
- **コードブロック**: 数式、コード、技術的内容は適切な言語指定で```ブロックで囲む
- **インラインコード**: 小さなコード片、ファイル名、変数名は`バッククォート`で囲む

### 3. 可読性向上
- **適切な空白**: セクション間、リスト項目間の適切な空行
- **行長制御**: 長すぎる行は適切な位置で改行
- **統一性**: 同種の要素は一貫したフォーマットで表現

### 4. 学術文書特有の要素
- **引用ブロック**: 重要な引用、定義は> ブロックで表現
- **表フォーマット**: データ、比較情報は適切な表形式で整理
- **リンクと参照**: URL、参考文献は適切なリンク形式で表現

### 5. 品質保証
- **情報無損失**: 原文のすべての情報を欠落なく保持
- **意味保全**: 原文の意図、ニュアンス、文脈を完全保持
- **技術精度**: 数学式、数値、専門用語の正確性確保

---

## 入力文書内容
{content}

上記内容を学術文書として最適な構造とフォーマットで整形し、
可読性、理解しやすさ、アクセシビリティを最大化した高品質Markdownを出力してください。
"""

openai_client = AzureOpenAIClient()
client = openai_client.get_openai_client()


async def analyze_document_process(file: UploadFile = File(...)):
    azure_client = AzureDocumentIntelligenceClient()
    client = azure_client.analyze_document_client()

    file_bytes = await file.read()         

    poller = client.begin_analyze_document(
        model_id="prebuilt-read",
        body=file_bytes,                    
        output_content_format="markdown",  
    )
    result = poller.result()
    result_dict = result.as_dict()
    save_output_file(result_dict)
    return {"result": result_dict}

async def structure_markdown(result_dict: dict):

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            ("user", USER_PROMPT)
        ]
    )
    chain = prompt | client.with_structured_output(
        StructureResultResponse
        )
    result = chain.invoke({"content": result_dict["result"]["content"]})
    return {
        "markdown": result.markdown
    }

async def process_pdf(file: UploadFile = File(...)):
    """
    PDF文書の包括的処理パイプライン。
    
    Azure Document Intelligence による文書分析と LLM による Markdown 整形を
    統合した高品質文書処理ワークフローを提供する。
    
    Parameters
    ----------
    file : UploadFile
        処理対象のPDFファイル（または他の対応文書形式）
        
    Returns
    -------
    Dict[str, str]
        最終的な構造化 Markdown 結果
        'markdown' キーに整形済み Markdown テキストを含む
    """
    # Step 1: Azure Document Intelligence による文書分析・テキスト抽出
    raw_analysis_result = await analyze_document_process(file)
    
    # Step 2: LLM による学術文書として最適化された Markdown 整形
    structured_markdown_result = await structure_markdown(raw_analysis_result)
    
    return structured_markdown_result
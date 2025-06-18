from fastapi import UploadFile, File
from libs.azure_client import AzureDocumentIntelligenceClient, AzureOpenAIClient
from app.services.shared.output_file import save_output_file
from langchain_core.prompts import ChatPromptTemplate
from app.schemas.schemas import StructureResultResponse
from app.services.proofreading.prompts.document_analysis_prompts import SYSTEM_PROMPT, USER_PROMPT

openai_client = AzureOpenAIClient()
client = openai_client.get_openai_client()


async def analyze_document_process(file: UploadFile = File(...)):
    """
    Azure Document Intelligence を使用してドキュメントを分析する
    
    Args:
        file: アップロードされたファイル
        
    Returns:
        dict: 分析結果辞書
    """
    azure_client = AzureDocumentIntelligenceClient()
    doc_client = azure_client.analyze_document_client()

    file_bytes = await file.read()         

    poller = doc_client.begin_analyze_document(
        model_id="prebuilt-read",
        body=file_bytes,                    
        output_content_format="markdown",  
    )
    result = poller.result()
    result_dict = result.as_dict()
    save_output_file(result_dict)
    return {"result": result_dict}


async def structure_markdown(result_dict: dict):
    """
    分析結果を構造化されたMarkdownに変換する
    
    Args:
        result_dict: Azure Document Intelligence の分析結果
        
    Returns:
        dict: 構造化されたMarkdown結果
    """
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
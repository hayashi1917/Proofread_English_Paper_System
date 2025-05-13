from fastapi import UploadFile, File
from libs.azure_client import AzureDocumentIntelligenceClient, AzureOpenAIClient
from app.services.utils.output_file import save_output_file
from langchain_core.prompts import ChatPromptTemplate
from app.schemas.schemas import StructureResultResponse
SYSTEM_PROMPT = """
あなたは、ドキュメントの内容を分析し、その内容をJSON形式で出力するプログラムです。
"""

USER_PROMPT = """
# 指示
以下のMarkdown形式のテキストをJSON形式に変換してください。

# ドキュメントの内容
{{content}}
"""


async def analyze_document_process(file: UploadFile = File(...)):
    azure_client = AzureDocumentIntelligenceClient()
    client = azure_client.analyze_document_client()

    file_bytes = await file.read()         

    poller = client.begin_analyze_document(
        model_id="prebuilt-layout",
        body=file_bytes,                    
        output_content_format="markdown",  
    )
    result = poller.result()
    result_dict = result.as_dict()
    save_output_file(result_dict)
    return {"result": result_dict}

async def structure_markdown(result_dict: dict):
    openai_client = AzureOpenAIClient()
    client = openai_client.get_openai_client()

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            ("user", USER_PROMPT)
        ]
    )
    chain = prompt | client.with_structured_output(
        StructureResultResponse
        )
    result = chain.invoke({"content": result_dict["content"]})
    return {
        "markdown": result.markdown
    }

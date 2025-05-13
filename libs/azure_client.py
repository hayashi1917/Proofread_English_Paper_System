from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

load_dotenv(".env.local")

class AzureDocumentIntelligenceClient:
    def __init__(self) -> None:
        self.client = DocumentIntelligenceClient(
            endpoint=os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT"),
            credential=AzureKeyCredential(os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")),
        )
        
    def analyze_document_client(self) -> DocumentIntelligenceClient:
        return self.client      

class AzureOpenAIClient:
    def __init__(self) -> None:
        self.client = ChatOpenAI(
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            model_name="gpt-4o-mini",
            temperature=0,
        )
    
    def get_openai_client(self) -> ChatOpenAI:
        return self.client


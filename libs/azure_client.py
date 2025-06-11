from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
from langchain_openai import ChatOpenAI
import openai
import os
from typing import List
from langchain.tools import BaseTool
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

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
    def __init__(self,tools: List[BaseTool] | None = None):
        # ★ 1) max_completion_tokens で“書き過ぎ”ブロック
        # ★ 2) tools / tool_choice をその場で bind できるようにする
        self.client = ChatOpenAI(
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            model_name="gpt-4.1-mini",
            temperature=0,
            max_completion_tokens=4096,
        )
        if tools:                          # tools が渡されていたら即 bind
            self.client = self.client.bind(
                tools=tools,
                tool_choice="auto"
            )

    def get_openai_client(self) -> ChatOpenAI:
        return self.client

class AzureOpenAIEmbeddings:
    def __init__(self):
        self.client = OpenAIEmbeddings(
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            model="text-embedding-ada-002",
        )

    def get_openai_embeddings(self) -> OpenAIEmbeddings:
        return self.client


class ChromaDBClient:
    def __init__(self):
        azure_embeddings_client = AzureOpenAIEmbeddings()
        self.client = Chroma(
            collection_name="knowledge_base_db",
            persist_directory="chroma_db",
            embedding_function=azure_embeddings_client.get_openai_embeddings(),
        )

    def get_chroma_client(self) -> Chroma:
        return self.client

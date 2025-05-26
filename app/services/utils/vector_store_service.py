from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document as LangchainDocument
from libs.azure_client import ChromaDBClient, AzureOpenAIEmbeddings
from typing import List
from app.schemas.schemas import KnowledgeFromLatex

class VectorStoreService:
    def __init__(self):
        self.chroma_client = ChromaDBClient().get_chroma_client()
        self.openai_embeddings = AzureOpenAIEmbeddings().get_openai_embeddings()
        self.collection_name = "knowledge_base_db"

    def add_knowledge_to_vector_store(self, knowledge_list: List[KnowledgeFromLatex]):
            documents_to_add: List[LangchainDocument] = []
            for knowledge_item in knowledge_list:
                page_content = knowledge_item.knowledge

                # ChromaDBのメタデータ値は string, int, float, bool である必要があります。
                # issue_category はリストなので、文字列に変換します (例:カンマ区切り)。
                issue_category_str = ", ".join(knowledge_item.issue_category) if knowledge_item.issue_category else None

                current_metadata: Dict[str, Any] = {
                    "issue_category": issue_category_str,
                    "reference_url": knowledge_item.reference_url,
                    "knowledge_type": knowledge_item.knowledge_type,
                }
                # None の値を持つキーをメタデータから除外する (ChromaDBがNoneを許容しない場合があるため)
                filtered_metadata = {k: v for k, v in current_metadata.items() if v is not None}

                doc = LangchainDocument(page_content=page_content, metadata=filtered_metadata)
                documents_to_add.append(doc)

            if documents_to_add:
                self.chroma_client.add_documents(documents=documents_to_add)

    def get_knowledge_from_vector_store(self, query: str, k: int = 10):
        results = self.chroma_client.similarity_search(query, k)
        return results
    
    def get_knowledge_from_vector_store_by_issue_category(self, query: str, issue_category: str):
        results = self.chroma_client.similarity_search(query, filter={"issue_category": issue_category})
        return results

    def get_knowledge_from_vector_store_by_knowledge_type(self, query: str, knowledge_type: str):
        results = self.chroma_client.similarity_search(query, filter={"knowledge_type": knowledge_type})
        return results

from libs.azure_client import AzureOpenAIClient
from app.services.knowledge.utils.vector_store_service import VectorStoreService

class ClientFactory:
    """クライアントインスタンスの一元管理"""
    
    _openai_client = None
    _vector_store = None
    
    @classmethod
    def get_openai_client(cls) -> AzureOpenAIClient:
        """Azure OpenAIクライアントのシングルトンインスタンスを取得"""
        if cls._openai_client is None:
            cls._openai_client = AzureOpenAIClient()
        return cls._openai_client
    
    @classmethod  
    def get_vector_store(cls) -> VectorStoreService:
        """ベクターストアサービスのシングルトンインスタンスを取得"""
        if cls._vector_store is None:
            cls._vector_store = VectorStoreService()
        return cls._vector_store
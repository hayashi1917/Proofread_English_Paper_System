from app.services.utils.vector_store_service import VectorStoreService

vector_store_service = VectorStoreService()

def search_knowledge_from_vector_store(query: str):
    knowledge_list = vector_store_service.get_knowledge_from_vector_store(query)
    return knowledge_list

def search_knowledge_from_vector_store_by_issue_category(query: str, issue_category: str):
    knowledge_list = vector_store_service.get_knowledge_from_vector_store_by_issue_category(query, issue_category)
    return knowledge_list

def search_knowledge_from_vector_store_by_knowledge_type(query: str, knowledge_type: str):
    knowledge_list = vector_store_service.get_knowledge_from_vector_store_by_knowledge_type(query, knowledge_type)
    return knowledge_list


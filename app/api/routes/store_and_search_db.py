from fastapi import APIRouter
from app.services.csv_to_db import csv_to_db
from app.services.search_knoeledge import search_knowledge_from_vector_store, delete_all_knowledge_from_vector_store
from app.schemas.schemas import SearchKnowledgeQuery

router = APIRouter(
    prefix="/store_and_search_db",
    tags=["store_and_search_db"],
)

@router.post("/store_knowledge")
async def store_knowledge(csv_file_name: str):
    return csv_to_db(csv_file_name)

@router.post("/search_knowledge")
async def search_knowledge(query: SearchKnowledgeQuery):
    return search_knowledge_from_vector_store(query.query)

@router.post("/delete_all_knowledge")
async def delete_all_knowledge():
    from app.services.search_knoeledge import delete_all_knowledge_from_vector_store
    return delete_all_knowledge_from_vector_store()
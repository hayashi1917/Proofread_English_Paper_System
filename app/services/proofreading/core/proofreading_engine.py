"""
校正処理のコアエンジン
"""
from typing import List, Tuple
from langchain.prompts import ChatPromptTemplate

from app.schemas.schemas import ProofreadResult
from app.services.shared.client_factory import ClientFactory
from app.services.shared.logging_utils import log_proofreading_debug
from app.services.proofreading.utils.proofreading_utils import (
    format_knowledge_snippet, 
    create_knowledge_block,
    get_search_parameters
)
from app.services.proofreading.prompts.proofreading_prompts import (
    PROOFREADING_SYSTEM_PROMPT,
    PROOFREADING_USER_PROMPT_WITH_KNOWLEDGE,
    PROOFREADING_SYSTEM_PROMPT_WITHOUT_KNOWLEDGE,
    PROOFREADING_USER_PROMPT_WITHOUT_KNOWLEDGE
)
from app.services.shared.exceptions import ProofreadingError

class ProofreadingEngine:
    """校正処理のコアエンジンクラス"""
    
    def __init__(self):
        self.openai_client = ClientFactory.get_openai_client()
        self.vector_store = ClientFactory.get_vector_store()
    
    def retrieve_knowledge_snippets(self, queries: List[str]) -> str:
        """
        クエリリストから関連知識を検索し、整形済み文字列として返す
        
        Args:
            queries (List[str]): 検索クエリのリスト
            
        Returns:
            str: 整形済み知識ブロック
        """
        try:
            cited_snippets: List[str] = []
            search_params = get_search_parameters()
            
            for query in queries:
                log_proofreading_debug("知識検索クエリ実行", query)
                docs = self.vector_store.get_knowledge_from_vector_store(
                    query, 
                    k=search_params["k"]
                )
                
                for doc in docs:
                    snippet = format_knowledge_snippet(
                        doc.page_content, 
                        doc.metadata.get('reference_url', 'Unknown')
                    )
                    cited_snippets.append(snippet)
            
            return create_knowledge_block(cited_snippets)
            
        except Exception as e:
            raise ProofreadingError(f"知識検索中にエラーが発生しました: {e}")
    
    def execute_proofreading_with_knowledge(
        self, 
        section_text: str, 
        knowledge_block: str
    ) -> ProofreadResult:
        """
        知識ベースを使用したLLM校正を実行
        
        Args:
            section_text (str): 校正対象テキスト
            knowledge_block (str): 参照知識ブロック
            
        Returns:
            ProofreadResult: 校正結果
        """
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", PROOFREADING_SYSTEM_PROMPT),
                ("user", PROOFREADING_USER_PROMPT_WITH_KNOWLEDGE),
            ])
            
            chain = prompt | self.openai_client.get_openai_client().with_structured_output(ProofreadResult)
            
            result: ProofreadResult = chain.invoke({
                "section_content": section_text,
                "knowledge_contents": knowledge_block
            })
            result.pre_proofread = section_text
            
            log_proofreading_debug("校正完了", {
                "original_length": len(section_text),
                "result_length": len(result.post_proofread)
            })
            
            return result
            
        except Exception as e:
            raise ProofreadingError(f"LLM校正処理中にエラーが発生しました: {e}")
    
    def execute_proofreading_without_knowledge(self, section_text: str) -> ProofreadResult:
        """
        知識ベースを使用しないLLM校正を実行
        
        Args:
            section_text (str): 校正対象テキスト
            
        Returns:
            ProofreadResult: 校正結果
        """
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", PROOFREADING_SYSTEM_PROMPT_WITHOUT_KNOWLEDGE),
                ("user", PROOFREADING_USER_PROMPT_WITHOUT_KNOWLEDGE),
            ])
            
            chain = prompt | self.openai_client.get_openai_client().with_structured_output(ProofreadResult)
            
            result: ProofreadResult = chain.invoke({
                "section_content": section_text
            })
            result.pre_proofread = section_text
            
            log_proofreading_debug("校正完了（知識ベースなし）", {
                "original_length": len(section_text),
                "result_length": len(result.post_proofread)
            })
            
            return result
            
        except Exception as e:
            raise ProofreadingError(f"LLM校正処理中にエラーが発生しました: {e}")
    
    def proofread_section_with_knowledge(
        self, 
        section_text: str, 
        queries: List[str]
    ) -> Tuple[ProofreadResult, str]:
        """
        知識ベースを使用してセクションを校正
        
        Args:
            section_text (str): 校正対象テキスト
            queries (List[str]): 検索クエリ
            
        Returns:
            Tuple[ProofreadResult, str]: 校正結果と使用した知識
        """
        log_proofreading_debug("セクション校正開始（知識ベースあり）")
        
        knowledge_block = self.retrieve_knowledge_snippets(queries)
        result = self.execute_proofreading_with_knowledge(section_text, knowledge_block)
        
        log_proofreading_debug("校正前テキスト", result.pre_proofread)
        log_proofreading_debug("校正結果", result.post_proofread)
        log_proofreading_debug("校正の根拠", result.description)
        
        return result, knowledge_block
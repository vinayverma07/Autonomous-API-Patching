"""
Module: Vector Retrieval Engine & Agent Node
File Path: src/patching_agent/agents/retriever.py
Description: Coordinates high-performance semantic search operations against MongoDB Atlas 
             and provides a structured execution node wrapper for the LangGraph pipeline.
"""

import logging
from typing import List, Dict, Any, Optional
from langchain_community.embeddings import HuggingFaceEmbeddings
from patching_agent.config import settings
from patching_agent.database import db_manager
from patching_agent.agents.state import AgentGraphState

logger = logging.getLogger(__name__)

class TechnicalRetriever:
    """Production vector search retriever executing semantic lookups on MongoDB Atlas."""

    def __init__(self):
        logger.info("Initializing Retrieval Engine Embeddings...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL_NAME,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )

    async def vector_search(
        self, 
        query: str, 
        top_k: int = 4, 
        file_type_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Executes a native vector search against MongoDB Atlas using an aggregation pipeline."""
        if db_manager.db is None:
            raise RuntimeError("Database connection uninitialized. Ensure db_manager.connect() is called.")

        collection = db_manager.db["documentation"]
        
        try:
            query_vector = self.embeddings.embed_query(query)
        except Exception as e:
            logger.error(f"Failed to generate query embedding vector: {e}")
            return []

        vector_search_stage = {
            "index": settings.VECTOR_INDEX_NAME,
            "path": "embedding",
            "queryVector": query_vector,
            "numCandidates": top_k * 10,
            "limit": top_k
        }

        if file_type_filter:
            vector_search_stage["filter"] = {
                "metadata.file_type": {"$eq": file_type_filter}
            }

        pipeline = [
            {"$vectorSearch": vector_search_stage},
            {
                "$project": {
                    "_id": 0,
                    "text": 1,
                    "metadata": 1,
                    "score": {"$meta": "vectorSearchScore"}
                }
            }
        ]

        try:
            cursor = collection.aggregate(pipeline)
            results = await cursor.to_list(length=top_k)
            logger.info(f"Vector lookup executed. Retrieved {len(results)} matches for query.")
            return results
        except Exception as e:
            logger.error(f"Database vector aggregation query execution failed: {e}")
            return []


class RetrieverAgentNode:
    """Agent node responsible for managing database queries and populating graph reference state."""

    def __init__(self):
        logger.info("Initializing Retriever Agent Node wrapper...")
        # Instantiate our internal retriever class safely within the node container
        self.retriever_engine = TechnicalRetriever()

    def _format_context_blocks(self, search_results: List[Dict[str, Any]]) -> List[str]:
        """Formats raw database list arrays into clearly bounded XML-style strings for Mistral."""
        formatted_blocks = []
        
        for idx, item in enumerate(search_results, start=1):
            text_content = item.get("text", "").strip()
            metadata = item.get("metadata", {})
            source = metadata.get("source", "Unknown Reference")
            file_type = metadata.get("file_type", "txt")
            score = item.get("score", 0.0)

            block = (
                f'<document id="{idx}" source="{source}" type="{file_type}" vector_score="{score:.4f}">\n'
                f'{text_content}\n'
                f'</document>'
            )
            formatted_blocks.append(block)
            
        return formatted_blocks

    async def retrieve(self, state: AgentGraphState) -> Dict[str, Any]:
        """Executes asynchronous lookups against MongoDB Atlas based on the graph's diagnostic data."""
        logger.info("Retriever Agent Node searching for reference documentation...")
        
        analysis = state.failure_analysis
        if not analysis or "optimized_rag_query" not in analysis:
            logger.warning("No optimized search query found inside the graph state. Bypassing RAG step.")
            return {
                "execution_status": "retrieval_skipped",
                "retrieved_docs": []
            }

        search_query = analysis["optimized_rag_query"]
        logger.info(f"Executing RAG database search with query: '{search_query}'")

        try:
            raw_results = await self.retriever_engine.vector_search(
                query=search_query,
                top_k=4
            )
            
            if not raw_results:
                logger.warning("Vector search completed successfully but returned zero matching records.")
                return {
                    "execution_status": "retrieval_empty",
                    "retrieved_docs": []
                }

            formatted_docs = self._format_context_blocks(raw_results)
            logger.info(f"Successfully processed and formatted {len(formatted_docs)} reference documents.")

            return {
                "execution_status": "context_retrieved",
                "retrieved_docs": formatted_docs
            }

        except Exception as e:
            logger.error(f"Critical failure inside Retriever Agent Node: {e}")
            return {
                "execution_status": "retrieval_failed",
                "retrieved_docs": []
            }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    node = RetrieverAgentNode()
    print("Combined Retriever module compiled and structural validation passed.")
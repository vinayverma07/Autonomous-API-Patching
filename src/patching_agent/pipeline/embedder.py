"""
Module: Local Vector Embedding Pipeline
Description: Transforms processed document chunks into high-dimensional semantic vectors 
             using BAAI/bge-small-en-v1.5 entirely offline, storing them in MongoDB Atlas.
"""

import logging
from typing import List
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
from patching_agent.config import settings
from patching_agent.database import db_manager

logger = logging.getLogger(__name__)

class TechnicalEmbedder:
    """Handles local embedding generation and database writing for our RAG pipeline."""

    def __init__(self):
        logger.info(f"Loading local embedding engine: {settings.EMBEDDING_MODEL_NAME}...")
        # HuggingFaceEmbeddings downloads and runs the model directly on your local hardware
        self.embeddings = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL_NAME,
            model_kwargs={'device': 'cpu'},  # Change to 'cuda' if you have a dedicated NVIDIA GPU
            encode_kwargs={'normalize_embeddings': True}  # True ensures Cosine Similarity calculation accuracy
        )

    async def embed_and_store(self, documents: List[Document]) -> int:
        """Vectorizes text documents and inserts them directly into MongoDB Atlas asynchronously."""
        if not documents:
            logger.warning("No documents provided for embedding storage.")
            return 0

        if db_manager.db is None:
            raise RuntimeError("Database connection is uninitialized. Call db_manager.connect() first.")

        collection = db_manager.db["documentation"]
        inserted_count = 0

        logger.info(f"Generating vectors for {len(documents)} document fragments...")

        # Extract text strings for batch embedding calculation
        texts = [doc.page_content for doc in documents]
        try:
            # Generate the vector matrices locally
            vector_arrays = self.embeddings.embed_documents(texts)
            
            payloads = []
            for i, doc in enumerate(documents):
                # Construct a clean, standardized BSON document structure for MongoDB Atlas Vector Search
                payload = {
                    "text": doc.page_content,
                    "embedding": vector_arrays[i],  # The array of 384 floats
                    "metadata": doc.metadata
                }
                payloads.append(payload)

            if payloads:
                # Insert chunks concurrently to maximize network throughput
                result = await collection.insert_many(payloads)
                inserted_count = len(result.inserted_ids)
                logger.info(f"Successfully saved {inserted_count} vector documents to Atlas.")

        except Exception as e:
            logger.error(f"Critical failure inside vector storage operation: {e}")
            raise e

        return inserted_count
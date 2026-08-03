import asyncio
import logging
from patching_agent.config import settings
from patching_agent.database import db_manager
from patching_agent.pipeline.ingestor import TechnicalIngestor
from patching_agent.pipeline.embedder import TechnicalEmbedder

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

async def main():
    logger.info("Connecting to MongoDB Atlas...")
    db_manager.connect()
    
    # 1. Parse and chunk technical files from the target directory
    docs_directory = "docs"
    logger.info(f"Scanning and parsing files from directory: '{docs_directory}'...")
    
    ingestor = TechnicalIngestor(chunk_size=600, chunk_overlap=60)
    documents = ingestor.ingest_directory(docs_directory)
    
    if not documents:
        logger.warning(f"No valid documents found in '{docs_directory}'. Please add .md or .py files to 'docs/'.")
        db_manager.disconnect()
        return

    # 2. Generate vector embeddings and store them in MongoDB Atlas
    logger.info(f"Generating embeddings and writing {len(documents)} document chunks to MongoDB Atlas...")
    embedder = TechnicalEmbedder()
    
    try:
        inserted_count = await embedder.embed_and_store(documents)
        logger.info(f"🎉 SUCCESS: Successfully stored {inserted_count} vector documents in the 'documentation' collection!")
    except Exception as e:
        logger.error(f"Failed to populate documentation collection: {e}")
    finally:
        db_manager.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
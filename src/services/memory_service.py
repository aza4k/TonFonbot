import uuid
import chromadb
from loguru import logger
from src.config import config

class MemoryService:
    def __init__(self, persistence_path: str = "./chroma_db"):
        """
        Initialize persistent ChromaDB client and collection.
        Uses default ChromaDB embeddings (all-MiniLM-L6-v2) running locally.
        """
        try:
            self.client = chromadb.PersistentClient(path=persistence_path)
            
            # Using default embedding function (no arguments needed usually, or sentence-transformers)
            # We rename collection to prompt a clean slate if needed, or rely on distinct naming
            # To be safe against dimension mismatch with old Gemini embeddings, let's use a new collection name 
            # OR wrap in try/except to handle potential dimension errors if user doesn't delete folder.
            # Let's use "ton_knowledge_base_local" to avoid conflict.
            
            self.collection = self.client.get_or_create_collection(
                name="ton_knowledge_base_v2", 
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"MemoryService initialized at {persistence_path} with collection 'ton_knowledge_base_v2'")
        except Exception as e:
            logger.error(f"Failed to initialize MemoryService: {e}")
            raise e

    async def check_similarity(self, text: str, threshold: float = 0.85) -> bool:
        """
        Checks if a similar memory exists (Duplicate detection).
        Returns True if similarity > threshold (default 85%).
        """
        try:
            # Chroma handles embedding automatically if we pass query_texts
            results = self.collection.query(
                query_texts=[text],
                n_results=1
            )

            if results and results['distances'] and len(results['distances'][0]) > 0:
                # In cosine space: distance = 1 - similarity
                # So similarity = 1 - distance
                distance = results['distances'][0][0]
                similarity = 1.0 - distance
                
                if similarity > threshold:
                    logger.info(f"Duplicate found! Similarity: {similarity:.2f} > {threshold}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error in check_similarity: {e}")
            return False

    async def save_memory(self, text: str, metadata: dict) -> bool:
        """
        Stores a text snippet with metadata into the knowledge base.
        Returns True if saved, False if failed.
        """
        try:
            doc_id = str(uuid.uuid4())
            self.collection.add(
                documents=[text],
                metadatas=[metadata],
                ids=[doc_id]
            )
            logger.info(f"Added memory {doc_id} to knowledge base.")
            return True
        except Exception as e:
            logger.error(f"Failed to add memory: {e}")
            return False

    # Alias for backward compatibility
    async def add_memory(self, text: str, metadata: dict):
        return await self.save_memory(text, metadata)

    async def query_memory(self, query: str, n_results: int = 5):
        """
        Retrieves relevant context for a query.
        """
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            return results
        except Exception as e:
            logger.error(f"Failed to query memory: {e}")
            return None

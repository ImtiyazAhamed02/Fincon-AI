# app/db/memory.py
# Stubbed out since memory service is not used in FINCON

from typing import List, Dict, Any
from app.core.logger import logger

class AIMemoryService:
    def __init__(self):
        logger.info("AIMemoryService initialized (SQLite stub).")

    def generate_embedding(self, text: str) -> List[float]:
        return [0.0] * 768

    def save_memory(self, user_id: str, content: str, metadata: Dict[str, Any] = None):
        logger.info(f"Stubbed save_memory called for user {user_id}.")
        return []

    def search_memory(self, user_id: str, query: str, limit: int = 5) -> List[Dict]:
        logger.info(f"Stubbed search_memory called for user {user_id}.")
        return []

memory_service = AIMemoryService()

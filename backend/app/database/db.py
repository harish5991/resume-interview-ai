import json
import os
import asyncio
import logging
from typing import Dict, Any, List, Optional
from backend.app.config import settings

logger = logging.getLogger("db")

class LocalJsonCollection:
    """A lightweight, file-persisted JSON collection mimicking Mongo collection API."""
    def __init__(self, name: str, data_dir: str):
        self.name = name
        self.file_path = os.path.join(data_dir, f"{name}.json")
        self._lock = asyncio.Lock()
        self._load()

    def _load(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    self.docs = json.load(f)
            except Exception as e:
                logger.warning(f"Error loading local collection {self.name}: {e}")
                self.docs = []
        else:
            self.docs = []

    def _save(self):
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.docs, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving local collection {self.name}: {e}")

    async def insert_one(self, doc: Dict[str, Any]):
        async with self._lock:
            doc_copy = dict(doc)
            if "_id" not in doc_copy:
                import uuid
                doc_copy["_id"] = str(uuid.uuid4())
            self.docs.append(doc_copy)
            self._save()
            return type("InsertResult", (), {"inserted_id": doc_copy["_id"]})()

    async def find_one(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        async with self._lock:
            for doc in self.docs:
                if all(doc.get(k) == v for k, v in query.items()):
                    return dict(doc)
            return None

    async def find(self, query: Optional[Dict[str, Any]] = None, limit: int = 200) -> List[Dict[str, Any]]:
        async with self._lock:
            if not query:
                return [dict(d) for d in self.docs[:limit]]
            res = []
            for doc in self.docs:
                if all(doc.get(k) == v for k, v in query.items()):
                    res.append(dict(doc))
                    if len(res) >= limit:
                        break
            return res

    async def update_one(self, query: Dict[str, Any], update: Dict[str, Any], upsert: bool = False):
        async with self._lock:
            for i, doc in enumerate(self.docs):
                if all(doc.get(k) == v for k, v in query.items()):
                    if "$set" in update:
                        self.docs[i].update(update["$set"])
                    else:
                        self.docs[i].update(update)
                    self._save()
                    return type("UpdateResult", (), {"modified_count": 1})()
            if upsert:
                new_doc = dict(query)
                if "$set" in update:
                    new_doc.update(update["$set"])
                else:
                    new_doc.update(update)
                if "_id" not in new_doc:
                    import uuid
                    new_doc["_id"] = str(uuid.uuid4())
                self.docs.append(new_doc)
                self._save()
                return type("UpdateResult", (), {"upserted_id": new_doc["_id"]})()
            return type("UpdateResult", (), {"modified_count": 0})()

    async def delete_one(self, query: Dict[str, Any]):
        async with self._lock:
            for i, doc in enumerate(self.docs):
                if all(doc.get(k) == v for k, v in query.items()):
                    del self.docs[i]
                    self._save()
                    return type("DeleteResult", (), {"deleted_count": 1})()
            return type("DeleteResult", (), {"deleted_count": 0})()

    async def delete_many(self, query: Dict[str, Any]):
        async with self._lock:
            original_len = len(self.docs)
            if not query:
                self.docs = []
            else:
                self.docs = [d for d in self.docs if not all(d.get(k) == v for k, v in query.items())]
            deleted = original_len - len(self.docs)
            self._save()
            return type("DeleteResult", (), {"deleted_count": deleted})()


class MongoCollectionWrapper:
    """Wraps an AsyncIOMotorCollection to provide identical async awaitable find/find_one API."""
    def __init__(self, motor_col):
        self.col = motor_col

    async def insert_one(self, doc: Dict[str, Any]):
        doc_copy = dict(doc)
        return await self.col.insert_one(doc_copy)

    async def find_one(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        res = await self.col.find_one(query)
        if res and "_id" in res:
            res["_id"] = str(res["_id"])
        return res

    async def find(self, query: Optional[Dict[str, Any]] = None, limit: int = 200) -> List[Dict[str, Any]]:
        q = query or {}
        cursor = self.col.find(q)
        docs = await cursor.to_list(length=limit)
        for d in docs:
            if "_id" in d:
                d["_id"] = str(d["_id"])
        return docs

    async def update_one(self, query: Dict[str, Any], update: Dict[str, Any], upsert: bool = False):
        return await self.col.update_one(query, update, upsert=upsert)

    async def delete_one(self, query: Dict[str, Any]):
        return await self.col.delete_one(query)

    async def delete_many(self, query: Dict[str, Any]):
        return await self.col.delete_many(query or {})


class DatabaseManager:
    def __init__(self):
        self.is_mongo = False
        self.mongo_client = None
        self.mongo_db = None
        self.collections: Dict[str, Any] = {}
        self.data_dir = settings.STORAGE_DIR
        os.makedirs(self.data_dir, exist_ok=True)

    async def connect(self):
        try:
            from motor.motor_asyncio import AsyncIOMotorClient
            client = AsyncIOMotorClient(settings.MONGODB_URI, serverSelectionTimeoutMS=1500)
            await client.server_info()
            self.mongo_client = client
            self.mongo_db = client[settings.DATABASE_NAME]
            self.is_mongo = True
            logger.info("Successfully connected to MongoDB.")
        except Exception as e:
            self.is_mongo = False
            logger.info(f"MongoDB not available ({e}). Using persistent Local JSON Database engine at {self.data_dir}.")

    def get_collection(self, name: str):
        if self.is_mongo and self.mongo_db is not None:
            if name not in self.collections:
                self.collections[name] = MongoCollectionWrapper(self.mongo_db[name])
            return self.collections[name]
        if name not in self.collections:
            self.collections[name] = LocalJsonCollection(name, self.data_dir)
        return self.collections[name]

db_manager = DatabaseManager()

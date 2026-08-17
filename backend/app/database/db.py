import json
import os
import asyncio
import logging
from typing import Dict, Any, List, Optional
from backend.app.config import settings

logger = logging.getLogger("db")

def _match_field(doc_val: Any, cond: Any) -> bool:
    if isinstance(cond, dict):
        for op, target in cond.items():
            if op == "$ne" and doc_val == target:
                return False
            elif op == "$eq" and doc_val != target:
                return False
            elif op == "$in" and (target is None or doc_val not in target):
                return False
            elif op == "$nin" and (target is not None and doc_val in target):
                return False
        return True
    return doc_val == cond

def _match_doc(doc: Dict[str, Any], query: Dict[str, Any]) -> bool:
    if not query:
        return True
    return all(_match_field(doc.get(k), v) for k, v in query.items())

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
                if _match_doc(doc, query):
                    return dict(doc)
            return None

    async def find(self, query: Optional[Dict[str, Any]] = None, limit: int = 200) -> List[Dict[str, Any]]:
        async with self._lock:
            if not query:
                return [dict(d) for d in self.docs[:limit]]
            res = []
            for doc in self.docs:
                if _match_doc(doc, query):
                    res.append(dict(doc))
                    if len(res) >= limit:
                        break
            return res

    async def update_one(self, query: Dict[str, Any], update: Dict[str, Any], upsert: bool = False):
        async with self._lock:
            for i, doc in enumerate(self.docs):
                if _match_doc(doc, query):
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
                if _match_doc(doc, query):
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
                self.docs = [d for d in self.docs if not _match_doc(d, query)]
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

    async def reset_ephemeral_sessions(self):
        """
        Wipes all non-default sessions and associated evaluations/histories,
        and initializes/resets the default session to a clean state.
        """
        from datetime import datetime, timezone
        col_sess = self.get_collection("sessions")
        col_evals = self.get_collection("evaluations")
        col_qh = self.get_collection("questions_history")
        col_final = self.get_collection("final_evaluations")
        col_saved = self.get_collection("saved_questions")

        # 1. Delete all non-default sessions and their associated records
        await col_sess.delete_many({"id": {"$ne": "default"}})
        await col_evals.delete_many({"session_id": {"$ne": "default"}})
        await col_qh.delete_many({"session_id": {"$ne": "default"}})
        await col_final.delete_many({"session_id": {"$ne": "default"}})
        await col_saved.delete_many({"session_id": {"$ne": "default"}})

        # 2. Reset or initialize default session cleanly
        now_str = datetime.now(timezone.utc).isoformat()
        clean_default = {
            "id": "default",
            "name": "Default Interview Prep",
            "created_at": now_str,
            "updated_at": now_str,
            "resume": None,
            "resume_score": None,
            "jd": None,
            "match": None,
            "questions": [],
            "saved_questions": [],
            "evaluations": [],
            "history": []
        }

        existing_default = await col_sess.find_one({"id": "default"})
        if existing_default:
            await col_sess.update_one(
                {"id": "default"},
                {"$set": {
                    "name": "Default Interview Prep",
                    "resume": None,
                    "resume_score": None,
                    "jd": None,
                    "match": None,
                    "questions": [],
                    "saved_questions": [],
                    "evaluations": [],
                    "history": [],
                    "updated_at": now_str
                }}
            )
        else:
            await col_sess.insert_one(clean_default)

        # Also clear any stale history from the default session
        await col_evals.delete_many({"session_id": "default"})
        await col_qh.delete_many({"session_id": "default"})
        await col_final.delete_many({"session_id": "default"})
        await col_saved.delete_many({"session_id": "default"})
        logger.info("Ephemeral sessions and data cleared. Default session initialized.")

db_manager = DatabaseManager()

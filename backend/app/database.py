import logging
from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient
import pymongo
from app.config import settings

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        self.is_connected = False
        self._in_memory_cache: Dict[str, Any] = {}
        self._in_memory_weather: Dict[str, Any] = {}
        self._in_memory_regions: Dict[str, Any] = {}

    async def connect(self):
        try:
            self.client = AsyncIOMotorClient(
                settings.MONGODB_URI,
                serverSelectionTimeoutMS=2000
            )
            # Check connection
            await self.client.admin.command('ping')
            self.db = self.client[settings.DATABASE_NAME]
            self.is_connected = True
            logger.info("Successfully connected to MongoDB.")
            
            # Create indexes
            await self.db.regions.create_index("region_id", unique=True)
            await self.db.weather_records.create_index(
                [("region_id", pymongo.ASCENDING), ("dataset", pymongo.ASCENDING), ("date", pymongo.ASCENDING)],
                unique=True
            )
            await self.db.analysis_cache.create_index("cache_key", unique=True)
            await self.db.analysis_cache.create_index("expires_at", expireAfterSeconds=0)
            logger.info("MongoDB indexes verified.")
        except Exception as e:
            logger.warning(f"Could not connect to live MongoDB: {e}. Falling back to in-memory store.")
            self.is_connected = False

    async def close(self):
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed.")

    # Cache operations
    async def get_cached_analysis(self, cache_key: str) -> Optional[Dict[str, Any]]:
        if self.is_connected and self.db is not None:
            try:
                doc = await self.db.analysis_cache.find_one({"cache_key": cache_key})
                if doc:
                    doc.pop("_id", None)
                    return doc
            except Exception as e:
                logger.error(f"MongoDB read error: {e}")
        return self._in_memory_cache.get(cache_key)

    async def save_cached_analysis(self, doc: Dict[str, Any]):
        cache_key = doc.get("cache_key")
        self._in_memory_cache[cache_key] = doc
        if self.is_connected and self.db is not None:
            try:
                await self.db.analysis_cache.replace_one(
                    {"cache_key": cache_key},
                    doc,
                    upsert=True
                )
            except Exception as e:
                logger.error(f"MongoDB save cache error: {e}")

    # Region operations
    async def save_region(self, region_doc: Dict[str, Any]):
        reg_id = region_doc.get("region_id")
        self._in_memory_regions[reg_id] = region_doc
        if self.is_connected and self.db is not None:
            try:
                await self.db.regions.replace_one(
                    {"region_id": reg_id},
                    region_doc,
                    upsert=True
                )
            except Exception as e:
                logger.error(f"MongoDB save region error: {e}")

    # Weather records caching
    async def get_weather_records(self, region_id: str, dataset: str, start_date: str, end_date: str):
        if self.is_connected and self.db is not None:
            try:
                cursor = self.db.weather_records.find({
                    "region_id": region_id,
                    "dataset": dataset,
                    "date": {"$gte": start_date, "$lte": end_date}
                }).sort("date", pymongo.ASCENDING)
                records = await cursor.to_list(length=40000)
                for r in records:
                    r.pop("_id", None)
                if records:
                    return records
            except Exception as e:
                logger.error(f"MongoDB get weather error: {e}")
        
        # In-memory check
        key_prefix = f"{region_id}:{dataset}:"
        results = [
            val for k, val in self._in_memory_weather.items()
            if k.startswith(key_prefix) and start_date <= val["date"] <= end_date
        ]
        return sorted(results, key=lambda x: x["date"]) if results else None

    async def save_weather_records(self, records: list):
        if not records:
            return
        for r in records:
            k = f"{r['region_id']}:{r['dataset']}:{r['date']}"
            self._in_memory_weather[k] = r
            
        if self.is_connected and self.db is not None:
            try:
                operations = [
                    pymongo.ReplaceOne(
                        {"region_id": r["region_id"], "dataset": r["dataset"], "date": r["date"]},
                        r,
                        upsert=True
                    )
                    for r in records
                ]
                if operations:
                    await self.db.weather_records.bulk_write(operations, ordered=False)
            except Exception as e:
                logger.error(f"MongoDB save weather records error: {e}")


db_manager = DatabaseManager()

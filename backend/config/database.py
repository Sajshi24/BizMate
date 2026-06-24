import logging
from typing import Optional

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConfigurationError, ConnectionFailure, PyMongoError

from backend.config.settings import DATABASE_NAME, MONGO_URI

logger = logging.getLogger(__name__)

_client: Optional[MongoClient] = None
_database: Optional[Database] = None


def get_client() -> MongoClient:
    """Return a shared MongoDB client, establishing the connection if needed."""
    global _client

    if _client is not None:
        return _client

    try:
        logger.info("Connecting to MongoDB at %s", MONGO_URI)
        _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        _client.admin.command("ping")
        logger.info("MongoDB connection established successfully")
    except ConnectionFailure as exc:
        logger.error("MongoDB connection failed: %s", exc)
        _client = None
        raise
    except ConfigurationError as exc:
        logger.error("Invalid MongoDB configuration: %s", exc)
        _client = None
        raise
    except PyMongoError as exc:
        logger.error("Unexpected MongoDB error during connection: %s", exc)
        _client = None
        raise

    return _client


def get_database() -> Database:
    """Return the configured application database."""
    global _database

    if _database is None:
        _database = get_client()[DATABASE_NAME]
        logger.info("Using MongoDB database: %s", DATABASE_NAME)

    return _database


class _LazyDatabase:
    """Proxy that lazily resolves to the shared database instance."""

    def __getattr__(self, name: str):
        return getattr(get_database(), name)

    def __getitem__(self, name: str):
        return get_database()[name]


db = _LazyDatabase()


def close_database() -> None:
    """Close the MongoDB client and reset cached handles."""
    global _client, _database

    if _client is not None:
        _client.close()
        logger.info("MongoDB connection closed")

    _client = None
    _database = None

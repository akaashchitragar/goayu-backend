from pymongo import MongoClient
from pymongo.database import Database
from app.core.config import settings
import ssl


class MongoDB:
    client: MongoClient = None
    db: Database = None


mongodb = MongoDB()


def connect_to_mongodb():
    """Connect to MongoDB"""
    try:
        # MongoDB connection with SSL/TLS configuration
        mongodb.client = MongoClient(
            settings.MONGODB_URI,
            tls=True,
            tlsAllowInvalidCertificates=True,
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=10000,
            socketTimeoutMS=10000,
        )
        mongodb.db = mongodb.client[settings.MONGODB_DB_NAME]
        # Test connection
        mongodb.client.admin.command('ping')
        print(f"✅ Connected to MongoDB: {settings.MONGODB_DB_NAME}")
    except Exception as e:
        print(f"❌ Error connecting to MongoDB: {e}")
        # Don't raise - allow app to start without DB
        print("⚠️  Application starting without database connection")


def close_mongodb_connection():
    """Close MongoDB connection"""
    if mongodb.client:
        mongodb.client.close()
        print("✅ MongoDB connection closed")


def get_database() -> Database:
    """Get MongoDB database instance"""
    return mongodb.db

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import UpdateOne
from bson import ObjectId

from config import MONGO_URI, DB_NAME


# =====================================================
# MONGODB
# =====================================================

mongo = AsyncIOMotorClient(
    MONGO_URI,
    serverSelectionTimeoutMS=10000,
    maxPoolSize=50,
    minPoolSize=5,
)

db = mongo[DB_NAME]

files = db.files
index_state = db.index_state


# =====================================================
# CREATE INDEXES
# =====================================================

async def create_indexes():

    # Exact title / prefix search
    await files.create_index(
        [("title_key", 1)],
        name="title_key"
    )

    # Multi-word token search
    await files.create_index(
        [("title_tokens", 1)],
        name="title_tokens"
    )

    # Title + year
    await files.create_index(
        [
            ("title_key", 1),
            ("year", 1)
        ],
        name="title_year"
    )

    # Title + language
    await files.create_index(
        [
            ("title_key", 1),
            ("language", 1)
        ],
        name="title_language"
    )

    # Prevent duplicate Telegram messages
    await files.create_index(
        [
            ("chat_id", 1),
            ("message_id", 1)
        ],
        unique=True,
        name="telegram_message_unique"
    )

    # Newest files
    await files.create_index(
        [("created_at", -1)],
        name="created_at"
    )

    print("MongoDB indexes ready.")


# =====================================================
# SAVE ONE FILE
# =====================================================

async def save_file(data):

    await files.update_one(
        {
            "chat_id": data["chat_id"],
            "message_id": data["message_id"]
        },
        {
            "$set": data
        },
        upsert=True
    )


# =====================================================
# BULK SAVE FILES
# =====================================================

async def save_files_bulk(data_list):

    if not data_list:
        return

    operations = []

    for data in data_list:

        operations.append(
            UpdateOne(
                {
                    "chat_id": data["chat_id"],
                    "message_id": data["message_id"]
                },
                {
                    "$set": data
                },
                upsert=True
            )
        )

    if operations:

        await files.bulk_write(
            operations,
            ordered=False
        )


# =====================================================
# GET FILE
# =====================================================

async def get_file(file_id):

    # Newer database IDs may be ObjectId strings.
    if isinstance(file_id, str):

        try:

            object_id = ObjectId(file_id)

            item = await files.find_one(
                {
                    "_id": object_id
                }
            )

            if item:
                return item

        except Exception:
            pass

    # Fallback for databases using string IDs.
    return await files.find_one(
        {
            "_id": file_id
        }
    )


# =====================================================
# COUNT FILES
# =====================================================

async def count_files():

    return await files.count_documents({})


# =====================================================
# EXACT SEARCH
# =====================================================

async def exact_search(
    title_key,
    limit=50
):

    cursor = (
        files
        .find(
            {
                "title_key": title_key
            }
        )
        .sort(
            [
                ("year", 1),
                ("message_id", 1)
            ]
        )
        .limit(limit)
    )

    return await cursor.to_list(
        length=limit
    )


# =====================================================
# PREFIX SEARCH
# =====================================================

async def prefix_search(
    title_key,
    limit=50
):

    import re

    escaped = re.escape(
        title_key
    )

    cursor = (
        files
        .find(
            {
                "title_key": {
                    "$regex": "^" + escaped
                }
            }
        )
        .sort(
            [
                ("title_key", 1),
                ("year", 1),
                ("message_id", 1)
            ]
        )
        .limit(limit)
    )

    return await cursor.to_list(
        length=limit
    )


# =====================================================
# TOKEN SEARCH
# =====================================================

async def token_search(
    tokens,
    limit=100
):

    if not tokens:
        return []

    cursor = (
        files
        .find(
            {
                "title_tokens": {
                    "$all": tokens
                }
            }
        )
        .limit(limit)
    )

    return await cursor.to_list(
        length=limit
    )


# =====================================================
# CONTAINS SEARCH
# =====================================================

async def contains_search(
    title_key,
    limit=100
):

    import re

    escaped = re.escape(
        title_key
    )

    cursor = (
        files
        .find(
            {
                "title_key": {
                    "$regex": escaped
                }
            }
        )
        .limit(limit)
    )

    return await cursor.to_list(
        length=limit
    )


# =====================================================
# INDEX CHECKPOINT
# =====================================================

async def get_index_state():

    data = await index_state.find_one(
        {
            "_id": "database_channel"
        }
    )

    if not data:

        return {
            "last_message_id": 0,
            "processed": 0,
            "indexed": 0,
            "skipped": 0,
            "running": False,
            "completed": False
        }

    return data


# =====================================================
# UPDATE INDEX CHECKPOINT
# =====================================================

async def update_index_state(
    last_message_id,
    processed=None,
    indexed=None,
    skipped=None,
    running=None,
    completed=None
):

    update = {
        "last_message_id": last_message_id
    }

    if processed is not None:
        update["processed"] = processed

    if indexed is not None:
        update["indexed"] = indexed

    if skipped is not None:
        update["skipped"] = skipped

    if running is not None:
        update["running"] = running

    if completed is not None:
        update["completed"] = completed

    await index_state.update_one(
        {
            "_id": "database_channel"
        },
        {
            "$set": update
        },
        upsert=True
    )


# =====================================================
# RESET INDEX
# =====================================================

async def reset_index_state():

    await index_state.update_one(
        {
            "_id": "database_channel"
        },
        {
            "$set": {
                "last_message_id": 0,
                "processed": 0,
                "indexed": 0,
                "skipped": 0,
                "running": False,
                "completed": False
            }
        },
        upsert=True
    )

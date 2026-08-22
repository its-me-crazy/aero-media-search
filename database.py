from bson import ObjectId
from bson.errors import InvalidId

from motor.motor_asyncio import AsyncIOMotorClient

from config import (
    MONGO_URI,
    DB_NAME
)


# =====================================================
# MONGODB
# =====================================================

mongo = AsyncIOMotorClient(
    MONGO_URI,
    serverSelectionTimeoutMS=10000,
    maxPoolSize=50,
    minPoolSize=5
)

db = mongo[DB_NAME]

files = db.files
index_state = db.index_state


# =====================================================
# CREATE INDEXES
# =====================================================

async def create_indexes():

    # Exact title lookup
    await files.create_index(
        [
            ("title_key", 1)
        ],
        name="title_key"
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

    # Telegram duplicate protection
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
        [
            ("created_at", -1)
        ],
        name="created_at"
    )

    # MongoDB text search
    try:

        await files.create_index(
            [
                ("title", "text"),
                ("filename", "text")
            ],
            name="title_text_search",
            default_language="none"
        )

    except Exception as e:

        print(
            "[TEXT INDEX]",
            repr(e)
        )

    print("MongoDB indexes ready.")


# =====================================================
# SAVE FILE
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
# GET FILE
# =====================================================

async def get_file(file_id):

    try:

        object_id = ObjectId(
            str(file_id)
        )

    except (InvalidId, TypeError):

        return None

    return await files.find_one(
        {
            "_id": object_id
        }
    )


# =====================================================
# COUNT
# =====================================================

async def count_files():

    return await files.count_documents({})


# =====================================================
# EXACT SEARCH
# =====================================================

async def exact_search(
    key,
    limit
):

    cursor = files.find(
        {
            "title_key": key
        }
    ).sort(
        [
            ("year", 1),
            ("message_id", 1)
        ]
    ).limit(limit)

    return await cursor.to_list(
        length=limit
    )


# =====================================================
# PREFIX SEARCH
# =====================================================

async def prefix_search(
    key,
    limit
):

    # Escape regex so user input cannot
    # become an expensive/invalid regex.

    import re

    escaped = re.escape(key)

    cursor = files.find(
        {
            "title_key": {
                "$regex": "^" + escaped
            }
        }
    ).sort(
        [
            ("title_key", 1),
            ("year", 1),
            ("message_id", 1)
        ]
    ).limit(limit)

    return await cursor.to_list(
        length=limit
    )


# =====================================================
# TEXT SEARCH
# =====================================================

async def text_search(
    query,
    limit
):

    if not query:
        return []

    try:

        cursor = files.find(
            {
                "$text": {
                    "$search": query
                }
            },
            {
                "score": {
                    "$meta": "textScore"
                }
            }
        ).sort(
            [
                (
                    "score",
                    {
                        "$meta": "textScore"
                    }
                ),
                (
                    "year",
                    1
                )
            ]
        ).limit(limit)

        return await cursor.to_list(
            length=limit
        )

    except Exception as e:

        print(
            "[TEXT SEARCH ERROR]",
            repr(e)
        )

        return []


# =====================================================
# INDEX STATE
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
# UPDATE INDEX STATE
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
        "last_message_id":
            last_message_id
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

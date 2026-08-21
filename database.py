from motor.motor_asyncio import AsyncIOMotorClient

from config import MONGO_URI, DB_NAME


mongo = AsyncIOMotorClient(
    MONGO_URI,
    serverSelectionTimeoutMS=10000
)

db = mongo[DB_NAME]

files = db.files
index_state = db.index_state


async def create_indexes():

    await files.create_index(
        [("title_key", 1)],
        name="title_key"
    )

    await files.create_index(
        [
            ("title_key", 1),
            ("year", 1)
        ],
        name="title_year"
    )

    await files.create_index(
        [
            ("title_key", 1),
            ("language", 1)
        ],
        name="title_language"
    )

    await files.create_index(
        [
            ("chat_id", 1),
            ("message_id", 1)
        ],
        unique=True,
        name="telegram_message_unique"
    )

    await files.create_index(
        [("created_at", -1)],
        name="created_at"
    )


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


async def get_file(file_id):

    return await files.find_one(
        {"_id": file_id}
    )


async def count_files():

    return await files.count_documents({})


async def exact_search(
    title_key,
    limit
):

    cursor = (
        files
        .find({
            "title_key": title_key
        })
        .sort([
            ("year", 1),
            ("message_id", 1)
        ])
        .limit(limit)
    )

    return await cursor.to_list(
        length=limit
    )


async def prefix_search(
    title_key,
    limit
):

    cursor = (
        files
        .find({
            "title_key": {
                "$regex": "^" + title_key
            }
        })
        .sort([
            ("title_key", 1),
            ("year", 1)
        ])
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
            "skipped": 0
        }

    return data


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

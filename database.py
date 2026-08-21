from motor.motor_asyncio import AsyncIOMotorClient

from config import MONGO_URI, DB_NAME


mongo = AsyncIOMotorClient(
    MONGO_URI,
    serverSelectionTimeoutMS=10000
)

db = mongo[DB_NAME]

files = db.files


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


async def exact_search(title_key, limit):

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


async def prefix_search(title_key, limit):

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

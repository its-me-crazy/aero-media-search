import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "").strip()

MONGO_URI = os.getenv("MONGO_URI", "").strip()
DB_NAME = os.getenv("DB_NAME", "aero_media_search").strip()

DATABASE_CHANNEL_ID = int(
    os.getenv("DATABASE_CHANNEL_ID", "0")
)

OWNER_ID = int(os.getenv("OWNER_ID", "0"))

BOT_USERNAME = os.getenv(
    "BOT_USERNAME", ""
).strip().lstrip("@")

UPDATES_USERNAME = os.getenv(
    "UPDATES_USERNAME",
    "Aero_Unity"
).strip().lstrip("@")

PORT = int(os.getenv("PORT", "10000"))

DELETE_AFTER = int(
    os.getenv("DELETE_AFTER", "300")
)

RESULTS_PER_PAGE = int(
    os.getenv("RESULTS_PER_PAGE", "10")
)

MAX_RESULTS = int(
    os.getenv("MAX_RESULTS", "50")
)


def validate_config():

    required = {
        "BOT_TOKEN": BOT_TOKEN,
        "API_ID": API_ID,
        "API_HASH": API_HASH,
        "MONGO_URI": MONGO_URI,
        "DATABASE_CHANNEL_ID": DATABASE_CHANNEL_ID,
        "OWNER_ID": OWNER_ID,
        "BOT_USERNAME": BOT_USERNAME,
    }

    missing = [
        key
        for key, value in required.items()
        if not value
    ]

    if missing:
        raise RuntimeError(
            "Missing environment variables: "
            + ", ".join(missing)
        )

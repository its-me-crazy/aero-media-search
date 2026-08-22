import os


# =====================================================
# ENVIRONMENT
# =====================================================

def env(name, default=""):
    return os.getenv(name, default).strip()


BOT_TOKEN = env("BOT_TOKEN")

API_ID = int(env("API_ID", "0"))
API_HASH = env("API_HASH")

MONGO_URI = env("MONGO_URI")
DB_NAME = env("DB_NAME", "aero_media_search")

DATABASE_CHANNEL_ID = int(
    env("DATABASE_CHANNEL_ID", "0")
)

OWNER_ID = int(
    env("OWNER_ID", "0")
)

BOT_USERNAME = env(
    "BOT_USERNAME"
).lstrip("@")

UPDATES_USERNAME = env(
    "UPDATES_USERNAME",
    "Aero_Unity"
).lstrip("@")

PORT = int(
    env("PORT", "10000")
)

DELETE_AFTER = int(
    env("DELETE_AFTER", "300")
)

RESULTS_PER_PAGE = int(
    env("RESULTS_PER_PAGE", "10")
)

MAX_RESULTS = int(
    env("MAX_RESULTS", "50")
)

INDEX_CHECKPOINT_EVERY = int(
    env("INDEX_CHECKPOINT_EVERY", "100")
)


# =====================================================
# VALIDATION
# =====================================================

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
        name
        for name, value in required.items()
        if not value
    ]

    if missing:
        raise RuntimeError(
            "Missing environment variables: "
            + ", ".join(missing)
        )

    if API_ID <= 0:
        raise RuntimeError(
            "API_ID must be a valid integer."
        )

    if DATABASE_CHANNEL_ID == 0:
        raise RuntimeError(
            "DATABASE_CHANNEL_ID is not configured."
        )

    if OWNER_ID == 0:
        raise RuntimeError(
            "OWNER_ID is not configured."
        )

    if not BOT_USERNAME:
        raise RuntimeError(
            "BOT_USERNAME is not configured."
        )

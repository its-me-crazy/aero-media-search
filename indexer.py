from datetime import datetime, timezone

from config import DATABASE_CHANNEL_ID

from database import save_file

from utils import (
    get_filename,
    extract_title,
    title_key,
    extract_year,
    detect_language,
    extract_quality,
    is_media
)


async def index_message(message):

    if not is_media(message):
        return False

    filename = get_filename(
        message
    )

    title = extract_title(
        filename
    )

    if not title:
        return False

    data = {

        "chat_id": message.chat.id,

        "message_id": message.id,

        "filename": filename,

        "title": title,

        "title_key": title_key(
            title
        ),

        "year": extract_year(
            filename
        ),

        "language": detect_language(
            filename
        ),

        "quality": extract_quality(
            filename
        ),

        "caption": message.caption or "",

        "media_type":
            "video"
            if message.video
            else
            "document"
            if message.document
            else
            "audio"
            if message.audio
            else
            "animation",

        "created_at":
            message.date
            or datetime.now(
                timezone.utc
            )
    }

    await save_file(
        data
    )

    return True


def register_indexer(app):

    @app.on_message(
        filters.channel
        & filters.chat(
            DATABASE_CHANNEL_ID
        )
    )
    async def database_listener(
        _,
        message
    ):

        try:

            if await index_message(
                message
            ):

                print(
                    "[INDEXED]",
                    message.id
                )

        except Exception as e:

            print(
                "[INDEX ERROR]",
                e
            )

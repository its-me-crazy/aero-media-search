from datetime import datetime, timezone

from pymongo import UpdateOne
from pyrogram import filters

from config import DATABASE_CHANNEL_ID

from database import (
    files,
    save_file,
    get_index_state,
    update_index_state
)

from utils import (
    get_filename,
    extract_title,
    title_key,
    title_tokens,
    extract_year,
    detect_language,
    extract_quality,
    is_media
)


# =====================================================
# SETTINGS
# =====================================================

BATCH_SIZE = 100


# =====================================================
# BUILD DOCUMENT
# =====================================================

def build_file_data(message):

    if not is_media(message):
        return None

    filename = get_filename(
        message
    )

    title = extract_title(
        filename
    )

    if not title:
        return None

    key = title_key(
        title
    )

    if not key:
        return None

    data = {

        "chat_id":
            message.chat.id,

        "message_id":
            message.id,

        "filename":
            filename,

        "title":
            title,

        "title_key":
            key,

        "title_tokens":
            title_tokens(title),

        "year":
            extract_year(filename),

        "language":
            detect_language(filename),

        "quality":
            extract_quality(filename),

        "caption":
            message.caption or "",

        "media_type":
            (
                "video"
                if message.video
                else
                "document"
                if message.document
                else
                "audio"
                if message.audio
                else
                "animation"
            ),

        "created_at":
            (
                message.date
                or datetime.now(timezone.utc)
            )
    }

    return data


# =====================================================
# INDEX ONE MESSAGE
# =====================================================

async def index_message(message):

    data = build_file_data(
        message
    )

    if not data:
        return False

    await save_file(
        data
    )

    return True


# =====================================================
# BULK INDEX
# =====================================================

async def bulk_index(
    messages
):

    if not messages:
        return 0, 0

    operations = []

    indexed = 0
    skipped = 0

    for message in messages:

        try:

            data = build_file_data(
                message
            )

            if not data:

                skipped += 1

                continue

            operations.append(
                UpdateOne(
                    {
                        "chat_id":
                            data["chat_id"],

                        "message_id":
                            data["message_id"]
                    },
                    {
                        "$set":
                            data
                    },
                    upsert=True
                )
            )

            indexed += 1

        except Exception as e:

            skipped += 1

            print(
                "[BUILD ERROR]",
                getattr(
                    message,
                    "id",
                    "unknown"
                ),
                repr(e)
            )

    if operations:

        try:

            await files.bulk_write(
                operations,
                ordered=False
            )

        except Exception as e:

            print(
                "[BULK WRITE ERROR]",
                repr(e)
            )

            # Fallback to individual writes.
            successful = 0

            for operation in operations:

                try:

                    await files.update_one(
                        operation._filter,
                        operation._doc,
                        upsert=True
                    )

                    successful += 1

                except Exception as single_error:

                    print(
                        "[SINGLE WRITE ERROR]",
                        repr(single_error)
                    )

            indexed = successful

    return indexed, skipped


# =====================================================
# INDEX EXISTING DATABASE CHANNEL
# =====================================================

async def index_existing_channel(
    app,
    status_callback=None
):

    state = await get_index_state()

    last_message_id = state.get(
        "last_message_id",
        0
    )

    processed = state.get(
        "processed",
        0
    )

    indexed = state.get(
        "indexed",
        0
    )

    skipped = state.get(
        "skipped",
        0
    )

    print(
        "================================"
    )

    print(
        "DATABASE INDEXING STARTED"
    )

    print(
        f"Starting from message ID: "
        f"{last_message_id}"
    )

    print(
        "================================"
    )

    await update_index_state(
        last_message_id,
        processed,
        indexed,
        skipped,
        True,
        False
    )

    batch = []

    try:

        async for message in app.get_chat_history(
            DATABASE_CHANNEL_ID,
            offset_id=last_message_id
        ):

            # -----------------------------------------
            # Skip checkpoint message
            # -----------------------------------------

            if (
                last_message_id
                and message.id == last_message_id
            ):
                continue

            batch.append(
                message
            )

            processed += 1

            # -----------------------------------------
            # PROCESS BATCH
            # -----------------------------------------

            if len(batch) >= BATCH_SIZE:

                batch_indexed, batch_skipped = (
                    await bulk_index(batch)
                )

                indexed += batch_indexed

                skipped += batch_skipped

                last_message_id = batch[-1].id

                batch.clear()

                # -------------------------------------
                # CHECKPOINT
                # -------------------------------------

                await update_index_state(
                    last_message_id,
                    processed,
                    indexed,
                    skipped,
                    True,
                    False
                )

                text = (
                    "📚 <b>Database Indexing...</b>\n\n"

                    f"📦 Processed: "
                    f"{processed:,}\n"

                    f"💾 Indexed: "
                    f"{indexed:,}\n"

                    f"⏭ Skipped: "
                    f"{skipped:,}\n\n"

                    f"🆔 Message ID: "
                    f"{last_message_id}"
                )

                print(
                    text
                )

                if status_callback:

                    try:

                        await status_callback(
                            text
                        )

                    except Exception as e:

                        print(
                            "[STATUS ERROR]",
                            repr(e)
                        )

        # =================================================
        # PROCESS REMAINING MESSAGES
        # =================================================

        if batch:

            batch_indexed, batch_skipped = (
                await bulk_index(batch)
            )

            indexed += batch_indexed

            skipped += batch_skipped

            last_message_id = batch[-1].id

            batch.clear()

            await update_index_state(
                last_message_id,
                processed,
                indexed,
                skipped,
                True,
                False
            )

        # =================================================
        # COMPLETED
        # =================================================

        await update_index_state(
            last_message_id,
            processed,
            indexed,
            skipped,
            False,
            True
        )

        text = (
            "✅ <b>Indexing Completed!</b>\n\n"

            f"📦 Processed: "
            f"{processed:,}\n"

            f"💾 Indexed: "
            f"{indexed:,}\n"

            f"⏭ Skipped: "
            f"{skipped:,}"
        )

        print(
            text
        )

        if status_callback:

            try:

                await status_callback(
                    text
                )

            except Exception as e:

                print(
                    "[STATUS ERROR]",
                    repr(e)
                )

        return {
            "processed": processed,
            "indexed": indexed,
            "skipped": skipped
        }

    except Exception as e:

        # =================================================
        # ERROR / STOPPED
        # =================================================

        await update_index_state(
            last_message_id,
            processed,
            indexed,
            skipped,
            False,
            False
        )

        print(
            "[INDEXING STOPPED]",
            repr(e)
        )

        if status_callback:

            try:

                await status_callback(

                    "⚠️ <b>Indexing stopped!</b>\n\n"

                    f"📦 Processed: "
                    f"{processed:,}\n"

                    f"💾 Indexed: "
                    f"{indexed:,}\n"

                    f"⏭ Skipped: "
                    f"{skipped:,}\n\n"

                    "Checkpoint saved.\n"

                    "Run <code>/index</code> again."
                )

            except Exception as callback_error:

                print(
                    "[CALLBACK ERROR]",
                    repr(callback_error)
                )

        return None


# =====================================================
# AUTOMATIC NEW FILE INDEXER
# =====================================================

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
                    "[NEW FILE INDEXED]",
                    message.id
                )

        except Exception as e:

            print(
                "[NEW FILE INDEX ERROR]",
                repr(e)
            )

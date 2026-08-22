import asyncio
from datetime import datetime, timezone

from pyrogram import filters

from config import (
    DATABASE_CHANNEL_ID,
    INDEX_CHECKPOINT_EVERY
)

from database import (
    save_file,
    get_index_state,
    update_index_state
)

from utils import (
    get_filename,
    extract_title,
    title_key,
    extract_year,
    detect_language,
    extract_quality,
    is_media
)


# =====================================================
# INDEX ONE MESSAGE
# =====================================================

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

    key = title_key(
        title
    )

    if not key:
        return False

    if message.video:

        media_type = "video"

    elif message.document:

        media_type = "document"

    elif message.audio:

        media_type = "audio"

    elif message.animation:

        media_type = "animation"

    else:

        return False

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

        "year":
            extract_year(filename),

        "language":
            detect_language(filename),

        "quality":
            extract_quality(filename),

        "caption":
            message.caption or "",

        "media_type":
            media_type,

        "created_at":
            message.date
            or datetime.now(timezone.utc)
    }

    await save_file(
        data
    )

    return True


# =====================================================
# INDEX EXISTING CHANNEL
# =====================================================

async def index_existing_channel(
    app,
    status_callback=None
):

    state = await get_index_state()

    last_message_id = int(
        state.get(
            "last_message_id",
            0
        )
    )

    processed = int(
        state.get(
            "processed",
            0
        )
    )

    indexed = int(
        state.get(
            "indexed",
            0
        )
    )

    skipped = int(
        state.get(
            "skipped",
            0
        )
    )

    print("================================")
    print("DATABASE INDEXING STARTED")
    print(
        f"Starting from message ID: "
        f"{last_message_id}"
    )
    print("================================")

    await update_index_state(
        last_message_id,
        processed,
        indexed,
        skipped,
        True,
        False
    )

    try:

        async for message in app.get_chat_history(
            DATABASE_CHANNEL_ID,
            offset_id=last_message_id
        ):

            if (
                last_message_id
                and message.id == last_message_id
            ):
                continue

            processed += 1

            try:

                success = await index_message(
                    message
                )

                if success:
                    indexed += 1
                else:
                    skipped += 1

            except Exception as e:

                skipped += 1

                print(
                    "[INDEX ERROR]",
                    message.id,
                    repr(e)
                )

            last_message_id = message.id

            # -----------------------------------------
            # CHECKPOINT
            # -----------------------------------------

            if (
                processed
                % INDEX_CHECKPOINT_EVERY
                == 0
            ):

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
                    f"{message.id}"
                )

                print(
                    text
                )

                if status_callback:

                    try:

                        await status_callback(
                            text
                        )

                    except Exception:
                        pass

            # Small yield
            await asyncio.sleep(
                0.01
            )

        # ---------------------------------------------
        # FINAL CHECKPOINT
        # ---------------------------------------------

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

            except Exception:
                pass

        return {
            "processed": processed,
            "indexed": indexed,
            "skipped": skipped
        }

    except Exception as e:

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

            except Exception:
                pass

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

            success = await index_message(
                message
            )

            if success:

                print(
                    "[NEW FILE INDEXED]",
                    message.id
                )

        except Exception as e:

            print(
                "[NEW FILE INDEX ERROR]",
                message.id,
                repr(e)
            )

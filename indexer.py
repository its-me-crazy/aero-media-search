import asyncio

from datetime import datetime, timezone

from pyrogram import filters

from config import DATABASE_CHANNEL_ID

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
            title_key(title),

        "year":
            extract_year(filename),

        "language":
            detect_language(filename),

        "quality":
            extract_quality(filename),

        "caption":
            message.caption or "",

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


# =====================================================
# EXISTING CHANNEL INDEXER
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

    # -----------------------------------------------
    # Mark indexing as running
    # -----------------------------------------------

    await update_index_state(

        last_message_id,

        processed=processed,

        indexed=indexed,

        skipped=skipped,

        running=True,

        completed=False
    )

    print(
        "================================"
    )

    print(
        "DATABASE INDEXING STARTED"
    )

    print(
        f"Resume message ID: "
        f"{last_message_id}"
    )

    print(
        "================================"
    )

    try:

        async for message in app.get_chat_history(

            DATABASE_CHANNEL_ID,

            offset_id=last_message_id
        ):

            processed += 1

            # ---------------------------------------
            # Index media
            # ---------------------------------------

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
                    "[INDEX MESSAGE ERROR]",
                    message.id,
                    repr(e)
                )

            # ---------------------------------------
            # SAVE CHECKPOINT
            # ---------------------------------------

            await update_index_state(

                message.id,

                processed=processed,

                indexed=indexed,

                skipped=skipped,

                running=True,

                completed=False
            )

            # ---------------------------------------
            # Console progress
            # ---------------------------------------

            if processed % 100 == 0:

                text = (

                    f"📚 Indexing...\n\n"

                    f"📦 Processed: "
                    f"{processed:,}\n"

                    f"💾 Indexed: "
                    f"{indexed:,}\n"

                    f"⏭ Skipped: "
                    f"{skipped:,}\n\n"

                    f"🆔 Last message: "
                    f"{message.id}"
                )

                print(text)

                if status_callback:

                    try:

                        await status_callback(
                            text
                        )

                    except Exception:

                        pass

            # ---------------------------------------
            # Small delay
            # ---------------------------------------

            await asyncio.sleep(
                0.02
            )

        # -------------------------------------------
        # COMPLETE
        # -------------------------------------------

        await update_index_state(

            last_message_id,

            processed=processed,

            indexed=indexed,

            skipped=skipped,

            running=False,

            completed=True
        )

        text = (

            "✅ <b>Indexing completed!</b>\n\n"

            f"📦 Processed: "
            f"{processed:,}\n"

            f"💾 Indexed: "
            f"{indexed:,}\n"

            f"⏭ Skipped: "
            f"{skipped:,}"
        )

        print(text)

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

            processed=processed,

            indexed=indexed,

            skipped=skipped,

            running=False,

            completed=False
        )

        print(
            "[INDEXING STOPPED]",
            repr(e)
        )

        if status_callback:

            try:

                await status_callback(

                    "⚠️ <b>Indexing stopped.</b>\n\n"

                    f"📦 Processed: "
                    f"{processed:,}\n"

                    f"💾 Indexed: "
                    f"{indexed:,}\n"

                    f"⏭ Skipped: "
                    f"{skipped:,}\n\n"

                    "The checkpoint was saved. "
                    "You can run <code>/index</code> "
                    "again to continue."
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

            if await index_message(
                message
            ):

                print(
                    "[NEW FILE INDEXED]",
                    message.id
                )

        except Exception as e:

            print(
                "[INDEX ERROR]",
                repr(e)
            )

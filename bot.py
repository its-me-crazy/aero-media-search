import asyncio
import time
import threading
from flask import Flask
from pyrogram import (
    Client,
    filters
)

from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

from pyrogram.errors import (
    UserIsBlocked,
    PeerIdInvalid,
    FloodWait
)

from config import (
    BOT_TOKEN,
    API_ID,
    API_HASH,
    DATABASE_CHANNEL_ID,
    OWNER_ID,
    BOT_USERNAME,
    UPDATES_USERNAME,
    PORT,
    DELETE_AFTER,
    RESULTS_PER_PAGE,
    MAX_RESULTS,
    validate_config
)

from database import (
    create_indexes,
    get_file,
    count_files
)

from indexer import (
    register_indexer,
    index_existing_channel
)

from search import (
    search_movies
)

from utils import title_key


validate_config()


# =====================================================
# WEB SERVER
# =====================================================

web = Flask(
    __name__
)


@web.route("/")
def home():

    return {
        "status": "online",
        "bot": BOT_USERNAME
    }


@web.route("/health")
def health():

    return {
        "status": "healthy"
    }


def run_web():

    from waitress import serve

    serve(
        web,
        host="0.0.0.0",
        port=PORT
    )


# =====================================================
# PYROGRAM
# =====================================================

app = Client(

    "aero_media_search",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    in_memory=True,
    workers=4
)

# =====================================================
# CONNECTION TEST
# =====================================================

@app.on_message(filters.private & filters.command("ping"))
async def ping_handler(_, message):

    print(
        "========== PING RECEIVED =========="
    )

    print(
        "User ID:",
        message.from_user.id
    )

    print(
        "Message:",
        message.text
    )

    await message.reply_text(
        "🏓 <b>Pong!</b>\n\n"
        "Telegram updates are working."
    )


# =====================================================
# CACHE
# =====================================================

SEARCH_CACHE = {}

CACHE_TIME = 120


def get_cache(query):

    item = SEARCH_CACHE.get(
        query
    )

    if not item:
        return None

    if (
        time.time()
        - item["time"]
        > CACHE_TIME
    ):

        SEARCH_CACHE.pop(
            query,
            None
        )

        return None

    return item["results"]


def put_cache(
    query,
    results
):

    SEARCH_CACHE[
        query
    ] = {

        "results": results,

        "time": time.time()
    }


# =====================================================
# START
# =====================================================

@app.on_message(
    filters.private
    & filters.command("start")
)
async def start_handler(
    _,
    message
):

    args = message.command[1:]

    # -----------------------------------------------
    # FILE DEEP LINK
    # -----------------------------------------------

    if args:

        payload = args[0]

        if payload.startswith(
            "file_"
        ):

            file_id = payload[
                5:
            ]

            await deliver_file(
                message.from_user.id,
                file_id
            )

            return

    # -----------------------------------------------
    # NORMAL START
    # -----------------------------------------------

    await message.reply_text(

        "<b>🎬 Aero Media Search</b>\n\n"

        "Send a movie title to search.\n\n"

        "<b>Example:</b>\n"
        "<code>Avengers Endgame</code>",

        reply_markup=
        InlineKeyboardMarkup([

            [

                InlineKeyboardButton(

                    "📢 Updates",

                    url=
                    f"https://t.me/"
                    f"{UPDATES_USERNAME}"
                )

            ]

        ])
    )


# =====================================================
# GROUP SEARCH
# =====================================================

@app.on_message(
    filters.group
    & filters.command("search")
)
async def group_search(
    _,
    message
):

    if len(
        message.command
    ) < 2:

        await message.reply_text(

            "🔎 <b>Usage:</b>\n"
            "<code>/search Avengers Endgame</code>"
        )

        return

    query = " ".join(
        message.command[1:]
    ).strip()

    await show_results(
        message,
        query
    )


# =====================================================
# PRIVATE SEARCH
# =====================================================

@app.on_message(
    filters.private
    & filters.text
    & ~filters.command(
        [
            "start",
            "index",
            "stats"
        ]
    )
)
async def private_search(
    _,
    message
):

    query = message.text.strip()

    if len(query) < 2:
        return

    await show_results(
        message,
        query
    )


# =====================================================
# SHOW RESULTS
# =====================================================

async def show_results(
    message,
    query
):

    key = title_key(
        query
    )

    results = get_cache(
        key
    )

    if results is None:

        results = await search_movies(

            query,

            MAX_RESULTS
        )

        put_cache(
            key,
            results
        )

    if not results:

        await message.reply_text(

            f"❌ No result found for "
            f"<b>{query}</b>."
        )

        return

    # -----------------------------------------------
    # GROUP BY TITLE
    # -----------------------------------------------

    first = results[0]

    title = first.get(
        "title",
        query
    )

    year = first.get(
        "year"
    )

    languages = sorted(
        {
            item.get(
                "language",
                "Unknown"
            )

            for item in results
        }
    )

    language_text = ", ".join(
        languages
    )

    text = (

        f"🔎 <b>{query}</b>\n\n"

        f"🎬 <b>Title:</b> "
        f"{title}\n"
    )

    if year:

        text += (
            f"📅 <b>Year:</b> "
            f"{year}\n"
        )

    text += (

        f"🌐 <b>Language:</b> "
        f"{language_text}\n\n"

        f"⚡ <b>Powered by:</b> "
        f"@{UPDATES_USERNAME}\n\n"

        f"━━━━━━━━━━━━━━━━━━\n\n"

        f"🎬 <b>Movies Files</b>"
    )

    buttons = []

    for item in results[
        :RESULTS_PER_PAGE
    ]:

        database_id = str(
            item["_id"]
        )

        item_title = item.get(
            "title",
            "File"
        )

        item_year = item.get(
            "year"
        )

        language = item.get(
            "language",
            "Unknown"
        )

        quality = item.get(
            "quality",
            "Unknown"
        )

        label = (
            f"🎬 {item_title}"
        )

        if item_year:

            label += (
                f" {item_year}"
            )

        label += (
            f" • {language}"
        )

        if quality != "Unknown":

            label += (
                f" • {quality}"
            )

        # -------------------------------------------
        # DEEP LINK
        # -------------------------------------------

        link = (

            f"https://t.me/"
            f"{BOT_USERNAME}"
            f"?start=file_"
            f"{database_id}"
        )

        buttons.append([

            InlineKeyboardButton(

                label[:64],

                url=link
            )

        ])

    buttons.append([

        InlineKeyboardButton(

            "📢 Updates",

            url=
            f"https://t.me/"
            f"{UPDATES_USERNAME}"
        )

    ])

    await message.reply_text(

        text,

        reply_markup=
        InlineKeyboardMarkup(
            buttons
        ),

        disable_web_page_preview=True
    )


# =====================================================
# DELIVER FILE
# =====================================================

async def deliver_file(
    user_id,
    database_id
):

    item = await get_file(
        database_id
    )

    if not item:

        await app.send_message(

            user_id,

            "❌ This file is no longer available."
        )

        return

    message_id = item[
        "message_id"
    ]

    try:

        # -------------------------------------------
        # COPY ORIGINAL TELEGRAM MESSAGE
        # -------------------------------------------

        sent = await app.copy_message(

            chat_id=user_id,

            from_chat_id=
            DATABASE_CHANNEL_ID,

            message_id=message_id
        )

        # -------------------------------------------
        # UPDATES BUTTON
        # -------------------------------------------

        info = await app.send_message(

            user_id,

            "<b>⚡ Powered by "
            "@Aero_Unity</b>\n\n"
            "📢 Join our Updates channel.",

            reply_markup=
            InlineKeyboardMarkup([

                [

                    InlineKeyboardButton(

                        "📢 Updates",

                        url=
                        f"https://t.me/"
                        f"{UPDATES_USERNAME}"
                    )

                ]

            ])
        )

        # -------------------------------------------
        # DELETE AFTER 5 MINUTES
        # -------------------------------------------

        asyncio.create_task(

            delete_after(

                user_id,

                sent.id
            )
        )

        asyncio.create_task(

            delete_after(

                user_id,

                info.id
            )
        )

    except UserIsBlocked:

        print(
            "User blocked bot:",
            user_id
        )

    except PeerIdInvalid:

        print(
            "Invalid user:",
            user_id
        )

    except FloodWait as e:

        await asyncio.sleep(
            e.value
        )

    except Exception as e:

        print(
            "[DELIVERY ERROR]",
            repr(e)
        )


# =====================================================
# AUTO DELETE
# =====================================================

async def delete_after(
    chat_id,
    message_id
):

    await asyncio.sleep(
        DELETE_AFTER
    )

    try:

        await app.delete_messages(

            chat_id,

            message_id
        )

    except Exception as e:

        print(
            "[DELETE ERROR]",
            repr(e)
        )


# =====================================================
# STATS
# =====================================================

@app.on_message(
    filters.private
    & filters.user(OWNER_ID)
    & filters.command("stats")
)
async def stats(
    _,
    message
):

    total = await count_files()

    await message.reply_text(

        "<b>📊 Database</b>\n\n"

        f"📁 Indexed files: "
        f"<code>{total:,}</code>"
    )


# =====================================================
# REGISTER DATABASE LISTENER
# =====================================================

register_indexer(
    app
)

# =====================================================
# INDEX EXISTING DATABASE
# =====================================================

INDEX_RUNNING = False


@app.on_message(
    filters.private
    & filters.user(OWNER_ID)
    & filters.command("index")
)
async def index_command(
    _,
    message
):

    global INDEX_RUNNING

    if INDEX_RUNNING:

        await message.reply_text(
            "⚠️ <b>Indexing is already running.</b>\n\n"
            "Please wait for it to finish."
        )

        return

    INDEX_RUNNING = True

    status = await message.reply_text(

        "📚 <b>Database indexing started...</b>\n\n"

        "This will scan your private database channel.\n\n"

        "⏳ Please wait..."
    )

    async def update_status(text):

        try:

            await status.edit_text(
                text
            )

        except Exception as e:

            print(
                "[STATUS UPDATE ERROR]",
                repr(e)
            )

    try:

        result = await index_existing_channel(

            app,

            status_callback=update_status
        )

        if result:

            await update_status(

                "✅ <b>Indexing completed!</b>\n\n"

                f"📦 Processed: "
                f"{result['processed']:,}\n"

                f"💾 Indexed: "
                f"{result['indexed']:,}\n"

                f"⏭ Skipped: "
                f"{result['skipped']:,}"
            )

    except Exception as e:

        print(
            "[INDEX COMMAND ERROR]",
            repr(e)
        )

        await update_status(

            "❌ <b>Indexing failed.</b>\n\n"

            f"<code>{e}</code>\n\n"

            "Run <code>/index</code> again "
            "to continue from the saved checkpoint."
        )

    finally:

        INDEX_RUNNING = False


@app.on_message()
async def debug_all_messages(_, message):

    print("================================")
    print("TELEGRAM UPDATE RECEIVED")
    print("Message ID:", message.id)

    if message.from_user:
        print("User ID:", message.from_user.id)

    if message.text:
        print("Text:", message.text)

    print("================================")
    
# =====================================================
# MAIN
# =====================================================

async def main():

    print("Starting Aero Media Search Bot...")

    await create_indexes()

    print("MongoDB indexes ready.")

    threading.Thread(
        target=run_web,
        daemon=True
    ).start()

    print("Web server started.")

    await app.start()

    print("================================")
    print("TELEGRAM BOT CONNECTED")

    me = await app.get_me()

    print(f"Bot ID: {me.id}")
    print(f"Bot Username: @{me.username}")

    print("================================")
    print("LISTENING FOR TELEGRAM UPDATES...")
    print("================================")

    try:
        response = requests.get(
            f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo",
            timeout=10
        )

        print("========== WEBHOOK CHECK ==========")
        print(response.json())
        print("===================================")

    except Exception as e:
        print(
            "[WEBHOOK CHECK ERROR]",
            repr(e)
        )

    try:

        await asyncio.Event().wait()

    finally:

        await app.stop()



if __name__ == "__main__":
    asyncio.run(main())

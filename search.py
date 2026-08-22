from database import (
    exact_search,
    prefix_search,
    text_search
)

from utils import title_key


async def search_movies(
    query,
    limit=50
):

    if not query:
        return []

    key = title_key(
        query
    )

    if not key:
        return []

    # =================================================
    # 1. EXACT
    # =================================================

    results = await exact_search(
        key,
        limit
    )

    if results:
        return results

    # =================================================
    # 2. PREFIX
    # =================================================

    results = await prefix_search(
        key,
        limit
    )

    if results:
        return results

    # =================================================
    # 3. TEXT SEARCH
    # =================================================

    results = await text_search(
        key,
        limit
    )

    return results

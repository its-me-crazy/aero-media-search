from database import (
    exact_search,
    prefix_search
)

from utils import title_key


async def search_movies(
    query,
    limit=50
):

    key = title_key(
        query
    )

    if not key:
        return []

    # First: exact title.
    results = await exact_search(
        key,
        limit
    )

    if results:
        return results

    # Second: prefix.
    results = await prefix_search(
        key,
        limit
    )

    return results

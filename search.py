import re

from database import (
    exact_search,
    prefix_search,
    token_search,
    contains_search
)

from utils import (
    title_key,
    title_tokens
)


# =====================================================
# SEARCH SCORE
# =====================================================

def score_result(
    item,
    query_key,
    query_tokens
):

    item_key = item.get(
        "title_key",
        ""
    )

    score = 0

    # Exact title
    if item_key == query_key:
        score += 1000

    # Starts with query
    elif item_key.startswith(
        query_key
    ):
        score += 700

    # Query contained in title
    elif query_key in item_key:
        score += 500

    item_tokens = set(
        item.get(
            "title_tokens",
            []
        )
    )

    query_token_set = set(
        query_tokens
    )

    # All words exist
    if query_token_set:

        matched = (
            query_token_set
            & item_tokens
        )

        score += (
            len(matched) * 100
        )

        if matched == query_token_set:
            score += 300

    # Prefer titles close in length
    difference = abs(
        len(item_key)
        - len(query_key)
    )

    score -= min(
        difference,
        100
    )

    return score


# =====================================================
# SEARCH MOVIES
# =====================================================

async def search_movies(
    query,
    limit=50
):

    query_key = title_key(
        query
    )

    if not query_key:
        return []

    query_tokens = title_tokens(
        query
    )

    # =================================================
    # 1. EXACT
    # =================================================

    results = await exact_search(
        query_key,
        limit
    )

    if results:

        results.sort(
            key=lambda item:
            score_result(
                item,
                query_key,
                query_tokens
            ),
            reverse=True
        )

        return results[:limit]

    # =================================================
    # 2. PREFIX
    # =================================================

    results = await prefix_search(
        query_key,
        limit
    )

    if results:

        results.sort(
            key=lambda item:
            score_result(
                item,
                query_key,
                query_tokens
            ),
            reverse=True
        )

        return results[:limit]

    # =================================================
    # 3. TOKEN SEARCH
    # =================================================

    if query_tokens:

        results = await token_search(
            query_tokens,
            min(limit * 3, 150)
        )

        if results:

            results.sort(
                key=lambda item:
                score_result(
                    item,
                    query_key,
                    query_tokens
                ),
                reverse=True
            )

            return results[:limit]

    # =================================================
    # 4. CONTAINS SEARCH
    # =================================================

    results = await contains_search(
        query_key,
        min(limit * 2, 100)
    )

    if results:

        results.sort(
            key=lambda item:
            score_result(
                item,
                query_key,
                query_tokens
            ),
            reverse=True
        )

        return results[:limit]

    return []

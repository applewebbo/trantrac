"""Smart categorization utilities: keyword extraction and category suggestions."""

import re

from django.db.models import F

ITALIAN_STOPWORDS = frozenset(
    {
        # articles
        "il",
        "lo",
        "la",
        "i",
        "gli",
        "le",
        "un",
        "uno",
        "una",
        # prepositions
        "di",
        "da",
        "in",
        "a",
        "su",
        "per",
        "tra",
        "fra",
        "con",
        "senza",
        # articulated prepositions
        "del",
        "dello",
        "della",
        "dei",
        "degli",
        "delle",
        "al",
        "allo",
        "alla",
        "ai",
        "agli",
        "alle",
        "dal",
        "dallo",
        "dalla",
        "dai",
        "dagli",
        "dalle",
        "nel",
        "nello",
        "nella",
        "nei",
        "negli",
        "nelle",
        "sul",
        "sullo",
        "sulla",
        "sui",
        "sugli",
        "sulle",
        # conjunctions / pronouns / misc
        "e",
        "ed",
        "o",
        "ma",
        "se",
        "che",
        "chi",
        "cui",
        "non",
        "pos",
        "via",
        "spa",
        "srl",
    }
)

MIN_KEYWORD_LENGTH = 3


def extract_first_significant_word(description: str) -> str:
    """Return the first non-stopword, non-trivial token from *description*.

    Splits on any non-alphanumeric character so that "ESSELUNGA-RIGNANO"
    correctly yields "esselunga" and "AMAZON.COM" yields "amazon".
    """
    if not description:
        return ""
    tokens = re.split(r"[^a-zA-Z0-9]", description.lower())
    for token in tokens:
        if len(token) >= MIN_KEYWORD_LENGTH and token not in ITALIAN_STOPWORDS:
            return token
    return ""


def get_category_suggestions(user, description: str, limit: int = 5) -> list[dict]:
    """Return category+subcategory suggestions for *description*.

    Priority order (highest first):
      1. UserKeywordPreference – personal learned mappings, sorted by count
      2. MerchantMapping – global pre-seeded merchant table

    Duplicate (category, subcategory) pairs are suppressed.
    Returns a list of dicts with keys:
        category_id, subcategory_id, subcategory_name, category_name
    """
    # Import here to avoid circular imports at module level
    from trantrac.models import MerchantMapping, UserKeywordPreference

    if not description:
        return []

    keyword = extract_first_significant_word(description)
    if not keyword:
        return []

    results: list[dict] = []
    seen: set[tuple[int, int]] = set()

    # 1. Personal preferences ordered by usage count (unique by constraint, no dedup needed)
    for pref in (
        UserKeywordPreference.objects.filter(user=user, keyword=keyword)
        .select_related("category", "subcategory")
        .order_by(F("count").desc())
    ):
        seen.add((pref.category_id, pref.subcategory_id))
        results.append(
            {
                "category_id": pref.category_id,
                "subcategory_id": pref.subcategory_id,
                "subcategory_name": pref.subcategory.name,
                "category_name": pref.category.name,
            }
        )
        if len(results) >= limit:
            return results

    # 2. Global merchant mappings (at most one result per keyword due to unique constraint)
    for mm in MerchantMapping.objects.filter(keyword=keyword).select_related(
        "category", "subcategory"
    ):
        pair = (mm.category_id, mm.subcategory_id)
        if pair not in seen:
            seen.add(pair)
            results.append(
                {
                    "category_id": mm.category_id,
                    "subcategory_id": mm.subcategory_id,
                    "subcategory_name": mm.subcategory.name,
                    "category_name": mm.category.name,
                }
            )

    return results[:limit]

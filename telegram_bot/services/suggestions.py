"""Smart subcategory suggestions based on user history and fuzzy matching"""

from datetime import timedelta

from django.db.models import Count
from django.utils import timezone
from rapidfuzz import fuzz

from trantrac.models import CategoryUsage, Subcategory


def get_subcategory_suggestions(
    user, description: str, limit: int = 5
) -> list[Subcategory]:
    """
    Get subcategory suggestions based on:
    1. User's most used subcategories in last 30 days
    2. Fuzzy match on description keywords

    Args:
        user: User instance
        description: Transaction description
        limit: Max number of suggestions (default 5)

    Returns:
        List of Subcategory instances, ordered by relevance
    """
    suggestions = []
    seen_ids = set()

    # Step 1: User's most used subcategories (last 30 days)
    cutoff_date = timezone.now() - timedelta(days=30)

    recent_usage = (
        CategoryUsage.objects.filter(
            user=user,
            created_at__gte=cutoff_date,
        )
        .values("subcategory")
        .annotate(usage_count=Count("id"))
        .order_by("-usage_count")[:limit]
    )

    for item in recent_usage:
        try:
            subcategory = Subcategory.objects.select_related("category").get(
                id=item["subcategory"]
            )
            if subcategory.id not in seen_ids:
                suggestions.append(subcategory)
                seen_ids.add(subcategory.id)
        except Subcategory.DoesNotExist:
            continue

    # Step 2: Fuzzy match on description (if we need more suggestions)
    if len(suggestions) < limit:
        description_lower = description.lower()
        all_subcategories = Subcategory.objects.select_related("category").all()

        # Calculate fuzzy scores for each subcategory
        scored_subcategories = []
        for subcat in all_subcategories:
            if subcat.id in seen_ids:
                continue

            # Fuzzy match on subcategory name
            score = fuzz.partial_ratio(description_lower, subcat.name.lower())

            if score > 60:  # Threshold for relevance
                scored_subcategories.append((score, subcat))

        # Sort by score (highest first) and add to suggestions
        scored_subcategories.sort(key=lambda x: x[0], reverse=True)

        for score, subcat in scored_subcategories[: limit - len(suggestions)]:
            suggestions.append(subcat)
            seen_ids.add(subcat.id)

    return suggestions[:limit]

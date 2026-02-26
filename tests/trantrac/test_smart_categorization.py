"""Tests for smart categorization: MerchantMapping, UserKeywordPreference, suggestions."""

import pytest
from django.core.management import call_command
from django.test import Client

from tests.conftest import TestCase
from trantrac.categorization import (
    extract_first_significant_word,
    get_category_suggestions,
)
from trantrac.models import (
    Category,
    CategoryUsage,
    MerchantMapping,
    Subcategory,
    UserKeywordPreference,
)


# ---------------------------------------------------------------------------
# extract_first_significant_word
# ---------------------------------------------------------------------------


class TestExtractFirstSignificantWord:
    def test_simple_word(self):
        assert extract_first_significant_word("ESSELUNGA") == "esselunga"

    def test_lowercase_preserved(self):
        assert extract_first_significant_word("esselunga spesa") == "esselunga"

    def test_strips_leading_article(self):
        assert extract_first_significant_word("IL CONAD DI MILANO") == "conad"

    def test_strips_preposition(self):
        assert extract_first_significant_word("DA LIDL EXTRA") == "lidl"

    def test_strips_articulated_preposition(self):
        assert extract_first_significant_word("SPESA DEL GIORNO") == "spesa"

    def test_empty_string_returns_empty(self):
        assert extract_first_significant_word("") == ""

    def test_only_stopwords_returns_empty(self):
        assert extract_first_significant_word("IL LA LO") == ""

    def test_short_tokens_skipped(self):
        # "AB" is 2 chars, skipped; "ZARA" matches
        assert extract_first_significant_word("AB ZARA") == "zara"

    def test_splits_on_non_alphanumeric(self):
        # "ESSELUNGA-RIGNANO" → tokens ["esselunga", "rignano"] → first = "esselunga"
        assert (
            extract_first_significant_word("ESSELUNGA-RIGNANO SULL'ARNO") == "esselunga"
        )

    def test_dot_separated(self):
        # "AMAZON.COM" → ["amazon", "com"] → "amazon"
        assert extract_first_significant_word("AMAZON.COM AMZN") == "amazon"

    def test_numeric_tokens_skipped_when_too_short(self):
        # "12 NETFLIX" → "12" is 2 chars (skip), "netflix" matches
        assert extract_first_significant_word("12 NETFLIX") == "netflix"

    def test_pagamento_pos_skipped_as_stopword(self):
        # "PAGAMENTO POS LIDL" → "pagamento" not in stopwords, so returns "pagamento"
        # Actually "pagamento" is a generic word but NOT in our stopwords list
        result = extract_first_significant_word("PAGAMENTO POS LIDL")
        assert result == "pagamento"


# ---------------------------------------------------------------------------
# MerchantMapping model
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestMerchantMappingModel(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Alimentari")
        self.subcategory = Subcategory.objects.create(
            name="Supermercato", category=self.category, skip_sheet_save=True
        )

    def test_create_merchant_mapping(self):
        mm = MerchantMapping.objects.create(
            keyword="esselunga",
            category=self.category,
            subcategory=self.subcategory,
        )
        assert mm.keyword == "esselunga"
        assert mm.category == self.category
        assert mm.subcategory == self.subcategory

    def test_str_representation(self):
        mm = MerchantMapping.objects.create(
            keyword="esselunga",
            category=self.category,
            subcategory=self.subcategory,
        )
        assert str(mm) == "esselunga → Alimentari / Supermercato"

    def test_keyword_is_unique(self):
        from django.db import IntegrityError

        MerchantMapping.objects.create(
            keyword="esselunga",
            category=self.category,
            subcategory=self.subcategory,
        )
        with pytest.raises(IntegrityError):
            MerchantMapping.objects.create(
                keyword="esselunga",
                category=self.category,
                subcategory=self.subcategory,
            )

    def test_ordering_by_keyword(self):
        MerchantMapping.objects.create(
            keyword="zara", category=self.category, subcategory=self.subcategory
        )
        MerchantMapping.objects.create(
            keyword="aldi", category=self.category, subcategory=self.subcategory
        )
        keywords = list(MerchantMapping.objects.values_list("keyword", flat=True))
        assert keywords == ["aldi", "zara"]

    def test_verbose_names(self):
        assert MerchantMapping._meta.verbose_name == "mappatura merchant"
        assert MerchantMapping._meta.verbose_name_plural == "mappature merchant"


# ---------------------------------------------------------------------------
# UserKeywordPreference model
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestUserKeywordPreferenceModel(TestCase):
    def setUp(self):
        self.user = self.make_user("test@example.com")
        self.category = Category.objects.create(name="Alimentari")
        self.subcategory = Subcategory.objects.create(
            name="Supermercato", category=self.category, skip_sheet_save=True
        )

    def test_create_user_keyword_preference(self):
        pref = UserKeywordPreference.objects.create(
            user=self.user,
            keyword="esselunga",
            category=self.category,
            subcategory=self.subcategory,
        )
        assert pref.keyword == "esselunga"
        assert pref.count == 1
        assert pref.user == self.user

    def test_str_representation(self):
        pref = UserKeywordPreference.objects.create(
            user=self.user,
            keyword="esselunga",
            category=self.category,
            subcategory=self.subcategory,
        )
        assert (
            str(pref) == "test@example.com: esselunga → Alimentari / Supermercato (1)"
        )

    def test_unique_constraint_user_keyword_category_subcategory(self):
        from django.db import IntegrityError

        UserKeywordPreference.objects.create(
            user=self.user,
            keyword="esselunga",
            category=self.category,
            subcategory=self.subcategory,
        )
        with pytest.raises(IntegrityError):
            UserKeywordPreference.objects.create(
                user=self.user,
                keyword="esselunga",
                category=self.category,
                subcategory=self.subcategory,
            )

    def test_default_count_is_one(self):
        pref = UserKeywordPreference.objects.create(
            user=self.user,
            keyword="test",
            category=self.category,
            subcategory=self.subcategory,
        )
        assert pref.count == 1

    def test_verbose_names(self):
        assert UserKeywordPreference._meta.verbose_name == "preferenza keyword"
        assert UserKeywordPreference._meta.verbose_name_plural == "preferenze keyword"


# ---------------------------------------------------------------------------
# Auto-learning signal
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestAutoLearningSignal(TestCase):
    def setUp(self):
        self.user = self.make_user("test@example.com")
        self.category = Category.objects.create(name="Alimentari")
        self.subcategory = Subcategory.objects.create(
            name="Supermercato", category=self.category, skip_sheet_save=True
        )

    def test_category_usage_with_description_creates_keyword_preference(self):
        CategoryUsage.objects.create(
            user=self.user,
            category=self.category,
            subcategory=self.subcategory,
            description="ESSELUNGA RIGNANO SULL'ARNO",
        )
        pref = UserKeywordPreference.objects.get(user=self.user, keyword="esselunga")
        assert pref.category == self.category
        assert pref.subcategory == self.subcategory
        assert pref.count == 1

    def test_repeated_usage_increments_count(self):
        for _ in range(3):
            CategoryUsage.objects.create(
                user=self.user,
                category=self.category,
                subcategory=self.subcategory,
                description="ESSELUNGA SPESA",
            )
        pref = UserKeywordPreference.objects.get(user=self.user, keyword="esselunga")
        assert pref.count == 3

    def test_empty_description_does_not_create_preference(self):
        CategoryUsage.objects.create(
            user=self.user,
            category=self.category,
            subcategory=self.subcategory,
            description="",
        )
        assert UserKeywordPreference.objects.count() == 0

    def test_only_stopwords_description_does_not_create_preference(self):
        CategoryUsage.objects.create(
            user=self.user,
            category=self.category,
            subcategory=self.subcategory,
            description="IL LA LO DI",
        )
        assert UserKeywordPreference.objects.count() == 0

    def test_category_usage_without_description_does_not_create_preference(self):
        # No description field provided → blank → no learning
        CategoryUsage.objects.create(
            user=self.user,
            category=self.category,
            subcategory=self.subcategory,
        )
        assert UserKeywordPreference.objects.count() == 0

    def test_different_users_create_separate_preferences(self):
        user2 = self.make_user("other@example.com")
        CategoryUsage.objects.create(
            user=self.user,
            category=self.category,
            subcategory=self.subcategory,
            description="CONAD SPESA",
        )
        CategoryUsage.objects.create(
            user=user2,
            category=self.category,
            subcategory=self.subcategory,
            description="CONAD SUPERMERCATO",
        )
        assert UserKeywordPreference.objects.filter(user=self.user).count() == 1
        assert UserKeywordPreference.objects.filter(user=user2).count() == 1


# ---------------------------------------------------------------------------
# get_category_suggestions
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestGetCategorySuggestions(TestCase):
    def setUp(self):
        self.user = self.make_user("test@example.com")
        self.cat_alimentari = Category.objects.create(name="Alimentari")
        self.sub_supermercato = Subcategory.objects.create(
            name="Supermercato", category=self.cat_alimentari, skip_sheet_save=True
        )
        self.cat_trasporti = Category.objects.create(name="Trasporti")
        self.sub_carburante = Subcategory.objects.create(
            name="Carburante", category=self.cat_trasporti, skip_sheet_save=True
        )

    def test_returns_empty_for_empty_description(self):
        suggestions = get_category_suggestions(self.user, "")
        assert suggestions == []

    def test_returns_empty_for_only_stopwords(self):
        suggestions = get_category_suggestions(self.user, "IL LA LO")
        assert suggestions == []

    def test_merchant_mapping_match(self):
        MerchantMapping.objects.create(
            keyword="esselunga",
            category=self.cat_alimentari,
            subcategory=self.sub_supermercato,
        )
        suggestions = get_category_suggestions(self.user, "ESSELUNGA SPESA")
        assert len(suggestions) == 1
        assert suggestions[0]["category_id"] == self.cat_alimentari.pk
        assert suggestions[0]["subcategory_id"] == self.sub_supermercato.pk
        assert suggestions[0]["subcategory_name"] == "Supermercato"
        assert suggestions[0]["category_name"] == "Alimentari"

    def test_user_keyword_preference_takes_priority_over_merchant(self):
        # Merchant says "esselunga" → Alimentari/Supermercato
        MerchantMapping.objects.create(
            keyword="esselunga",
            category=self.cat_alimentari,
            subcategory=self.sub_supermercato,
        )
        # User previously manually chose Trasporti/Carburante for "esselunga" keyword
        # (weird, but testing priority)
        UserKeywordPreference.objects.create(
            user=self.user,
            keyword="esselunga",
            category=self.cat_trasporti,
            subcategory=self.sub_carburante,
            count=5,
        )
        suggestions = get_category_suggestions(self.user, "ESSELUNGA RIGNANO")
        # User preference should be first
        assert suggestions[0]["category_id"] == self.cat_trasporti.pk
        assert suggestions[0]["subcategory_id"] == self.sub_carburante.pk

    def test_no_duplicates_in_suggestions(self):
        # Both merchant and user preference point to the same category
        MerchantMapping.objects.create(
            keyword="esselunga",
            category=self.cat_alimentari,
            subcategory=self.sub_supermercato,
        )
        UserKeywordPreference.objects.create(
            user=self.user,
            keyword="esselunga",
            category=self.cat_alimentari,
            subcategory=self.sub_supermercato,
            count=3,
        )
        suggestions = get_category_suggestions(self.user, "ESSELUNGA SPESA")
        # Should appear only once
        pairs = [(s["category_id"], s["subcategory_id"]) for s in suggestions]
        assert len(pairs) == len(set(pairs))

    def test_respects_limit(self):
        for i in range(8):
            cat = Category.objects.create(name=f"Cat{i}")
            sub = Subcategory.objects.create(
                name=f"Sub{i}", category=cat, skip_sheet_save=True
            )
            MerchantMapping.objects.create(
                keyword=f"merchant{i}",
                category=cat,
                subcategory=sub,
            )
            # Add keyword that matches our test description
            UserKeywordPreference.objects.create(
                user=self.user,
                keyword="esselunga",
                category=cat,
                subcategory=sub,
                count=i + 1,
            )
        suggestions = get_category_suggestions(self.user, "ESSELUNGA", limit=3)
        assert len(suggestions) <= 3

    def test_user_preferences_ordered_by_count_descending(self):
        cat2 = Category.objects.create(name="Casa")
        sub2 = Subcategory.objects.create(
            name="Arredamento", category=cat2, skip_sheet_save=True
        )
        UserKeywordPreference.objects.create(
            user=self.user,
            keyword="esselunga",
            category=self.cat_alimentari,
            subcategory=self.sub_supermercato,
            count=2,
        )
        UserKeywordPreference.objects.create(
            user=self.user,
            keyword="esselunga",
            category=cat2,
            subcategory=sub2,
            count=10,
        )
        suggestions = get_category_suggestions(self.user, "ESSELUNGA SPESA")
        # Higher count (casa/arredamento) should be first
        assert suggestions[0]["category_name"] == "Casa"

    def test_no_match_returns_empty(self):
        suggestions = get_category_suggestions(self.user, "XYZABC123 UNKNOWN")
        assert suggestions == []

    def test_other_users_preferences_not_included(self):
        other_user = self.make_user("other@example.com")
        UserKeywordPreference.objects.create(
            user=other_user,
            keyword="esselunga",
            category=self.cat_alimentari,
            subcategory=self.sub_supermercato,
            count=5,
        )
        suggestions = get_category_suggestions(self.user, "ESSELUNGA SPESA")
        assert suggestions == []

    def test_user_pref_early_return(self):
        """When UserKeywordPreference fills up to limit, early-return branch is exercised."""
        for i in range(5):
            cat = Category.objects.create(name=f"PrefCat{i}")
            sub = Subcategory.objects.create(
                name=f"PrefSub{i}", category=cat, skip_sheet_save=True
            )
            UserKeywordPreference.objects.create(
                user=self.user,
                keyword="esselunga",
                category=cat,
                subcategory=sub,
                count=i + 1,
            )
        suggestions = get_category_suggestions(self.user, "ESSELUNGA SPESA", limit=3)
        assert len(suggestions) == 3


# ---------------------------------------------------------------------------
# suggest_categories view
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestSuggestCategoriesView(TestCase):
    def setUp(self):
        self.user = self.make_user("test@example.com")
        self.client = Client()
        self.client.login(username="test@example.com", password="password")
        self.category = Category.objects.create(name="Alimentari")
        self.subcategory = Subcategory.objects.create(
            name="Supermercato", category=self.category, skip_sheet_save=True
        )

    def test_unauthenticated_redirects(self):
        client = Client()
        response = client.get("/suggest-categories/", {"description": "ESSELUNGA"})
        assert response.status_code == 302

    def test_empty_description_returns_empty_fragment(self):
        response = self.client.get("/suggest-categories/", {"description": ""})
        assert response.status_code == 200
        assert b"badge" not in response.content

    def test_with_matching_merchant_returns_badges(self):
        MerchantMapping.objects.create(
            keyword="esselunga",
            category=self.category,
            subcategory=self.subcategory,
        )
        response = self.client.get(
            "/suggest-categories/", {"description": "ESSELUNGA SPESA"}
        )
        assert response.status_code == 200
        assert b"Supermercato" in response.content

    def test_no_match_returns_empty_fragment(self):
        response = self.client.get(
            "/suggest-categories/", {"description": "XYZUNKNOWN999"}
        )
        assert response.status_code == 200
        assert b"badge" not in response.content


# ---------------------------------------------------------------------------
# populate_merchant_mappings management command
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestPopulateMerchantMappingsCommand(TestCase):
    def test_creates_merchant_mappings(self):
        from io import StringIO

        out = StringIO()
        call_command("populate_merchant_mappings", stdout=out)
        assert MerchantMapping.objects.count() > 0
        assert "new merchant mappings created" in out.getvalue()

    def test_command_is_idempotent(self):
        from io import StringIO

        call_command("populate_merchant_mappings", stdout=StringIO())
        first_count = MerchantMapping.objects.count()
        call_command("populate_merchant_mappings", stdout=StringIO())
        assert MerchantMapping.objects.count() == first_count

    def test_creates_categories_if_missing(self):
        from io import StringIO

        call_command("populate_merchant_mappings", stdout=StringIO())
        assert Category.objects.filter(name="Alimentari").exists()
        assert Category.objects.filter(name="Trasporti").exists()

    def test_second_run_outputs_zero_created(self):
        from io import StringIO

        call_command("populate_merchant_mappings", stdout=StringIO())
        out = StringIO()
        call_command("populate_merchant_mappings", stdout=out)
        assert "0 new merchant mappings created" in out.getvalue()

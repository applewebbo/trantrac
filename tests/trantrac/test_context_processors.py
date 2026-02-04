import pytest
from django.test import RequestFactory

from trantrac.context_processors import crispy_css_container


@pytest.mark.django_db
class TestCrispyCssContainer:
    def test_crispy_css_container_returns_dict(self):
        """Test crispy_css_container returns dict with css_container"""
        request = RequestFactory().get("/")
        result = crispy_css_container(request)

        assert isinstance(result, dict)
        assert "css_container" in result

    def test_crispy_css_container_contains_custom_css(self):
        """Test css_container has custom CSS configuration"""
        from crispy_tailwind.tailwind import CSSContainer

        request = RequestFactory().get("/")
        result = crispy_css_container(request)

        assert isinstance(result["css_container"], CSSContainer)

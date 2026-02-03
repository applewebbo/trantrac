import pytest
from crispy_tailwind.tailwind import CSSContainer

from trantrac.crispy_config import CUSTOM_CSS_CONTAINER, base_input, custom_styles


@pytest.mark.django_db
class TestCrispyConfig:
    def test_base_input_contains_required_classes(self):
        """Test base_input contains required CSS classes"""
        assert "bg-base-200" in base_input
        assert "dark:bg-base-300" in base_input
        assert "border" in base_input
        assert "rounded-lg" in base_input

    def test_custom_styles_has_all_field_types(self):
        """Test custom_styles contains all standard field types"""
        expected_types = [
            "text",
            "number",
            "email",
            "password",
            "textarea",
            "date",
            "select",
            "checkbox",
        ]
        for field_type in expected_types:
            assert field_type in custom_styles

    def test_custom_styles_text_uses_base_input(self):
        """Test text field uses base_input styling"""
        assert custom_styles["text"] == base_input

    def test_custom_styles_number_uses_base_input(self):
        """Test number field uses base_input styling"""
        assert custom_styles["number"] == base_input

    def test_custom_styles_has_error_border(self):
        """Test custom_styles has error_border configuration"""
        assert "error_border" in custom_styles
        assert "red" in custom_styles["error_border"]

    def test_custom_css_container_is_instance_of_css_container(self):
        """Test CUSTOM_CSS_CONTAINER is instance of CSSContainer"""
        assert isinstance(CUSTOM_CSS_CONTAINER, CSSContainer)

    def test_custom_styles_empty_for_hidden_fields(self):
        """Test hidden field types have empty styling"""
        assert custom_styles["hidden"] == ""
        assert custom_styles["multiplehidden"] == ""

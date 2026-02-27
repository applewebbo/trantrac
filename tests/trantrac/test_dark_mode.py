import pytest

from tests.conftest import TestCase


@pytest.mark.django_db
class TestDarkMode(TestCase):
    def setUp(self):
        self.user = self.make_user("test@example.com")

    def _get_index(self):
        with self.login(username=self.user.email, password="password"):
            return self.get("index")

    def test_anti_flash_script_in_head(self):
        """Anti-flash script reads theme from localStorage before page renders"""
        response = self._get_index()
        content = response.content.decode()
        # Script must appear before </head>
        head_end = content.index("</head>")
        head_section = content[:head_end]
        assert "localStorage" in head_section
        assert "data-theme" in head_section

    def test_theme_toggle_button_present(self):
        """Theme toggle button is present in the navbar"""
        response = self._get_index()
        self.assertContains(response, 'id="theme-toggle"')

    def test_theme_toggle_function_present(self):
        """toggleTheme JS function is included in the page"""
        response = self._get_index()
        self.assertContains(response, "toggleTheme")

    def test_theme_icons_present(self):
        """Both sun and moon icons are present for theme switching"""
        response = self._get_index()
        self.assertContains(response, 'id="theme-icon-moon"')
        self.assertContains(response, 'id="theme-icon-sun"')

    def test_emerald_and_dim_themes_referenced(self):
        """The two configured themes are referenced in the toggle logic"""
        response = self._get_index()
        content = response.content.decode()
        assert "emerald" in content
        assert "dim" in content

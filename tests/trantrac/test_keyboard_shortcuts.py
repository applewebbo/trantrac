import pytest

from tests.conftest import TestCase


@pytest.mark.django_db
class TestKeyboardShortcuts(TestCase):
    def setUp(self):
        self.user = self.make_user("test@example.com")

    def _get_index(self):
        with self.login(username=self.user.email, password="password"):
            return self.get("index")

    def test_keyboard_help_dialog_rendered(self):
        """Keyboard help dialog element is present in the page"""
        response = self._get_index()
        self.assertContains(response, 'id="keyboard-help"')

    def test_keyboard_help_dialog_is_dialog_element(self):
        """Keyboard help uses a <dialog> element"""
        response = self._get_index()
        self.assertContains(response, "<dialog")
        self.assertContains(response, 'id="keyboard-help"')

    def test_keyboard_shortcut_n_listed(self):
        """Shortcut 'n' is listed in the help dialog"""
        response = self._get_index()
        content = response.content.decode()
        assert 'id="keyboard-help"' in content
        assert ">n<" in content or '"n"' in content or "'n'" in content

    def test_keyboard_shortcut_question_mark_listed(self):
        """Shortcut '?' is listed in the help dialog"""
        response = self._get_index()
        content = response.content.decode()
        assert "?" in content

    def test_keyboard_shortcuts_script_present(self):
        """Keyboard shortcuts JS is included in the page"""
        response = self._get_index()
        self.assertContains(response, "keyboard-help")
        self.assertContains(response, "keydown")

    def test_keyboard_shortcut_hint_in_footer(self):
        """Footer shows discoverability hint for keyboard shortcuts"""
        response = self._get_index()
        self.assertContains(response, "Premi ? per gli shortcut")

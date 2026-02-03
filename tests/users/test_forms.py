import pytest

from users.forms import CustomLoginForm


@pytest.mark.django_db
class TestCustomLoginForm:
    def test_custom_login_form_removes_password_help_text(self):
        """Test CustomLoginForm removes password help text"""
        form = CustomLoginForm()
        assert form.fields["password"].help_text == ""

    def test_custom_login_form_has_login_field(self):
        """Test CustomLoginForm has login field (email)"""
        form = CustomLoginForm()
        assert "login" in form.fields

    def test_custom_login_form_has_password_field(self):
        """Test CustomLoginForm has password field"""
        form = CustomLoginForm()
        assert "password" in form.fields

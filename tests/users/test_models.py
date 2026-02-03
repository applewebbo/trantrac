import pytest
from django.db import IntegrityError

from users.models import User


@pytest.mark.django_db
class TestUserModel:
    def test_create_user_with_email(self, create_user):
        """Test creating user with email"""
        user = create_user(email="test@example.com", password="testpass123")
        assert user.email == "test@example.com"
        assert user.check_password("testpass123")
        assert not user.is_staff
        assert not user.is_superuser
        assert user.username is None

    def test_create_user_with_display_name(self):
        """Test creating user with display name"""
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            display_name="John Doe",
        )
        assert user.display_name == "John Doe"

    def test_create_user_without_email_raises_error(self):
        """Test creating user without email raises ValueError"""
        with pytest.raises(ValueError, match="Users require an email field"):
            User.objects.create_user(email="", password="testpass123")

    def test_create_superuser(self):
        """Test creating superuser"""
        user = User.objects.create_superuser(
            email="admin@example.com", password="adminpass123"
        )
        assert user.email == "admin@example.com"
        assert user.is_staff
        assert user.is_superuser
        assert user.check_password("adminpass123")

    def test_create_superuser_with_is_staff_false_raises_error(self):
        """Test creating superuser with is_staff=False raises ValueError"""
        with pytest.raises(ValueError, match="Superuser must have is_staff=True"):
            User.objects.create_superuser(
                email="admin@example.com", password="adminpass123", is_staff=False
            )

    def test_create_superuser_with_is_superuser_false_raises_error(self):
        """Test creating superuser with is_superuser=False raises ValueError"""
        with pytest.raises(ValueError, match="Superuser must have is_superuser=True"):
            User.objects.create_superuser(
                email="admin@example.com", password="adminpass123", is_superuser=False
            )

    def test_email_is_unique(self, create_user):
        """Test that email must be unique"""
        create_user(email="test@example.com")
        with pytest.raises(IntegrityError):
            create_user(email="test@example.com")

    def test_user_str_returns_email(self, create_user):
        """Test user __str__ returns email"""
        user = create_user(email="test@example.com")
        assert str(user) == "test@example.com"

    def test_email_normalization(self):
        """Test email is normalized"""
        user = User.objects.create_user(
            email="Test@EXAMPLE.COM", password="testpass123"
        )
        assert user.email == "Test@example.com"

    def test_username_field_is_email(self):
        """Test USERNAME_FIELD is email"""
        assert User.USERNAME_FIELD == "email"

    def test_required_fields_is_empty(self):
        """Test REQUIRED_FIELDS is empty"""
        assert User.REQUIRED_FIELDS == []

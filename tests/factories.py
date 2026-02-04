import factory.django

from users.models import User


class UserFactory(factory.django.DjangoModelFactory):
    """
    Factory for creating User instances.
    Compatible with test_plus.TestCase.make_user().
    Note: password setting is handled by make_user(), not by this factory.
    """

    class Meta:
        model = User

    email = factory.Sequence(lambda n: "user_%d@test.com" % n)
    display_name = "Test User"

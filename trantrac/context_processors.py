from django.conf import settings

from trantrac.crispy_config import CUSTOM_CSS_CONTAINER


def crispy_css_container(request):
    """Add custom CSS container for crispy forms with dark mode support."""
    return {"css_container": CUSTOM_CSS_CONTAINER}


def app_version(request):
    """Expose APP_VERSION to all templates."""
    return {"app_version": settings.APP_VERSION}

from trantrac.crispy_config import CUSTOM_CSS_CONTAINER


def crispy_css_container(request):
    """Add custom CSS container for crispy forms with dark mode support."""
    return {"css_container": CUSTOM_CSS_CONTAINER}

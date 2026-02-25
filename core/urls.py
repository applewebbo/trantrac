from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def health_check(request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("", include("pwa.urls")),
    path("admin/", admin.site.urls),
    path("health/", health_check, name="health_check"),
    path("", include("trantrac.urls")),
    path("users/", include("users.urls")),
    path("telegram/", include("telegram_bot.urls")),
    path("__reload__/", include("django_browser_reload.urls")),
    path("invitations/", include("invitations.urls", namespace="invitations")),
    path("accounts/", include("allauth.urls")),
]

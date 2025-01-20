from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("trantrac.urls")),
    path("__reload__/", include("django_browser_reload.urls")),
    path("accounts/", include("allauth.urls")),
]

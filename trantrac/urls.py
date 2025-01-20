from django.urls import path

from trantrac import views

urlpatterns = [
    path("", views.index, name="index"),
]

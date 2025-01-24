from django.urls import path

from trantrac import views

urlpatterns = [
    path("", views.index, name="index"),
    path("add_category/", views.add_category, name="add_category"),
]

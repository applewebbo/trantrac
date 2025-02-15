from django.urls import path

from trantrac import views

urlpatterns = [
    path("", views.index, name="index"),
    path("add_category/", views.add_category, name="add_category"),
    path("add-subcategory/", views.add_subcategory, name="add_subcategory"),
    path("upload_csv/", views.upload_csv, name="upload_csv"),
    path("load_subcategory/", views.load_subcategories, name="load_subcategories"),
    path("refresh-categories/", views.refresh_categories, name="refresh_categories"),
]

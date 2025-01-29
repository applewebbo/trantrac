from django.contrib import admin

from trantrac.models import Category, Account, Subcategory

admin.site.register(Category)
admin.site.register(Subcategory)
admin.site.register(Account)

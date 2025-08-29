from django.urls import path
from .views import search_codes, most_common
urlpatterns = [
    path("search/", search_codes, name="codes-search"),
    path("most_common/", most_common, name="codes-most-common"),
]

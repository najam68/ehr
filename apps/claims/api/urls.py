from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DenialViewSet, workqueue

router = DefaultRouter()
router.register(r"denials", DenialViewSet, basename="denial")

urlpatterns = [
    path("workqueue/", workqueue, name="denial-workqueue"),
    path("", include(router.urls)),
]

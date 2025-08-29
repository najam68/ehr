from rest_framework.routers import DefaultRouter
from .views import SpecialtyViewSet, CareSettingViewSet, ClinicViewSet

router = DefaultRouter()
router.register(r"specialties", SpecialtyViewSet, basename="specialty")
router.register(r"caresettings", CareSettingViewSet, basename="caresetting")
router.register(r"clinics", ClinicViewSet, basename="clinic")

urlpatterns = router.urls

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from Accounts.views import HomeView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", HomeView, name="welcomepage"),
    path("betterself/Accounts/", include("Accounts.urls")),
    path("betterself/time-manager/", include("Time_Manager.urls")),
    path("betterself/wellbeing/", include("WellBeing.urls")),
    path("betterself/inventory/", include("Inventory.urls")),
    path("betterself/finance/", include("Finance_Wealth.urls")),
    path("betterself/finance/mpesa/", include("mpesa.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

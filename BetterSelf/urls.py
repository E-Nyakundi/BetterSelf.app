from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from Accounts.views import HomeView  # Ensure correct import

urlpatterns = [
    #path('accounts/', include('allauth.urls')),
    path("admin/", admin.site.urls),
    path("", HomeView, name="welcomepage"),  # If class-based
    path("betterself/Accounts/", include("Accounts.urls")),
    #path("betterself/finance-wealth/", include("Finance_Wealth.urls")),
    path('accounts/', include('allauth.urls')),
    path("betterself/time-manager/", include("Time_Manager.urls")),
    #path("betterself/wellbeing/", include("WellBeing.urls")),
]#+static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 
#+static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
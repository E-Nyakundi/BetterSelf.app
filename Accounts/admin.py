from django.contrib import admin

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'email', 'email_verified', 'auth_provider', 'title', 'created_at')
    search_fields = ('user__username', 'user__email', 'email', 'title', 'firebase_uid')
    list_filter = ('created_at', 'auth_provider', 'email_verified')
    readonly_fields = ('created_at', 'firebase_uid')

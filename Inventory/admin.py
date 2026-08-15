from django.contrib import admin

from .models import Category, Item


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'full_path', 'user')
    list_filter = ('user',)
    search_fields = ('name', 'parent__name', 'user__username')
    ordering = ('parent__id', 'name')
    autocomplete_fields = ['parent', 'user']

    def full_path(self, obj):
        return obj.full_path()
    full_path.short_description = 'Full Path'


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'category_path', 'condition', 'item_type', 'date_acquired')
    list_filter = ('condition', 'category', 'user')
    search_fields = ('name', 'category__name', 'user__username', 'purpose', 'item_type')
    date_hierarchy = 'date_acquired'
    autocomplete_fields = ['user', 'category']
    ordering = ('-date_acquired',)

    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'user', 'category')
        }),
        ('Item Details', {
            'fields': ('condition', 'date_acquired', 'purpose', 'item_type'),
            'classes': ('collapse',)
        }),
    )

    def category_path(self, obj):
        return obj.category.full_path() if obj.category else "Uncategorized"
    category_path.short_description = "Category"

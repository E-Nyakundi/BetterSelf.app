from django.contrib import admin
from .models import FinancialGoal


@admin.register(FinancialGoal)
class FinancialGoalAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'category', 'target_amount', 'current_amount', 'target_date')
    list_filter = ('category',)
    search_fields = ('name', 'user__username')

from django.contrib import admin
from .models import JournalEntry

# Register your models here.
class JournalAdmin(admin.ModelAdmin):
    list_display = ['days_date', 'time_of_day', 'entry']
    
    

admin.site.register(JournalEntry, JournalAdmin)
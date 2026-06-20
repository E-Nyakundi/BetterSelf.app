from django.urls import path
from .views import JournalView

urlpatterns = [
    path('journal/', JournalView.as_view(), name='journal'),
    path('journal/<int:journal_id>/', JournalView.as_view(), name='edit_journal'),
]

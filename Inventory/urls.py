from django.urls import path
from .views import (
    InventoryDashboardView,
    CategoryCreateView, CategoryDeleteView, CategoryListView,
    ItemCreateView, ItemDetailView, ItemDisposeView, ItemListView, ItemUpdateView,
)

urlpatterns = [
    path('', InventoryDashboardView.as_view(), name='inventory-dashboard'),
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('categories/create/', CategoryCreateView.as_view(), name='category-create'),
    path('categories/<int:pk>/delete/', CategoryDeleteView.as_view(), name='category-delete'),
    path('items/', ItemListView.as_view(), name='item-list'),
    path('items/create/', ItemCreateView.as_view(), name='item-create'),
    path('items/<int:pk>/', ItemDetailView.as_view(), name='item-detail'),
    path('items/<int:pk>/edit/', ItemUpdateView.as_view(), name='item-edit'),
    path('items/<int:pk>/dispose/', ItemDisposeView.as_view(), name='item-dispose'),
]

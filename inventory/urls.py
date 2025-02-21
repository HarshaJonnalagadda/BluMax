from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InventoryCategoryViewSet, InventoryItemViewSet, StockTransactionViewSet

# Create router and register viewsets
router = DefaultRouter()
router.register(r'categories', InventoryCategoryViewSet)
router.register(r'items', InventoryItemViewSet)
router.register(r'transactions', StockTransactionViewSet)

urlpatterns = [
    path('', include(router.urls)),  # API base path
]
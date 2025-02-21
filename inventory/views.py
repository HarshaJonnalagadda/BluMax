from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.timezone import now
from django.db.models import F, Q
from .models import InventoryCategory, InventoryItem, StockTransaction, DispensedItem
from .serializers import (
    InventoryCategorySerializer, 
    InventoryItemSerializer, 
    StockTransactionSerializer,
)
from billing.models import Invoice

class InventoryCategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for managing inventory categories."""
    queryset = InventoryCategory.objects.all()
    serializer_class = InventoryCategorySerializer
    permission_classes = []  # Set appropriate permissions

class InventoryItemViewSet(viewsets.ModelViewSet):
    """ViewSet for managing inventory items."""
    queryset = InventoryItem.objects.all()
    serializer_class = InventoryItemSerializer
    permission_classes = []

    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Retrieve items that are low in stock."""
        items = InventoryItem.objects.filter(quantity__lte=F('reorder_level'))
        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def expired(self, request):
        """Retrieve expired inventory items."""
        items = InventoryItem.objects.filter(expiry_date__lte=now(), is_active=True)
        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search inventory items based on name, category, or stock level."""
        query = request.query_params.get('query', '')
        category_id = request.query_params.get('category_id')
        low_stock = request.query_params.get('low_stock', 'false').lower() == 'true'
        expired = request.query_params.get('expired', 'false').lower() == 'true'

        items = InventoryItem.objects.all()
        
        if query:
            items = items.filter(Q(name__icontains=query) | Q(category__name__icontains=query))
        if category_id:
            items = items.filter(category_id=category_id)
        if low_stock:
            items = items.filter(quantity__lte=F('reorder_level'))
        if expired:
            items = items.filter(expiry_date__lte=now(), is_active=True)

        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def dispense(self, request, pk=None):
        """Dispense an inventory item and generate an invoice entry."""
        item = self.get_object()
        quantity = int(request.data.get('quantity', 0))
        invoice_id = request.data.get('invoice_id')

        if quantity <= 0:
            return Response({"detail": "Quantity must be greater than zero."}, status=status.HTTP_400_BAD_REQUEST)

        if item.quantity < quantity:
            return Response({"detail": "Insufficient stock available."}, status=status.HTTP_400_BAD_REQUEST)

        invoice = Invoice.objects.get(id=invoice_id)
        dispensed_item = DispensedItem.objects.create(
            invoice=invoice,
            item=item,
            quantity=quantity
        )

        return Response({"detail": "Item dispensed successfully.", "dispensed_item": dispensed_item.id}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def refund(self, request, pk=None):
        """Process a refund for a returned medication and update stock."""
        item = self.get_object()
        quantity = int(request.data.get('quantity', 0))
        invoice_id = request.data.get('invoice_id')

        if quantity <= 0:
            return Response({"detail": "Quantity must be greater than zero."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            invoice = Invoice.objects.get(id=invoice_id)
            dispensed_item = DispensedItem.objects.get(invoice=invoice, item=item)
        except (Invoice.DoesNotExist, DispensedItem.DoesNotExist):
            return Response({"detail": "Invoice or dispensed item not found."}, status=status.HTTP_404_NOT_FOUND)

        if quantity > dispensed_item.quantity:
            return Response({"detail": "Cannot refund more than dispensed quantity."}, status=status.HTTP_400_BAD_REQUEST)

        dispensed_item.quantity -= quantity
        if dispensed_item.quantity == 0:
            dispensed_item.delete()
        else:
            dispensed_item.save()

        # Restore stock level
        item.quantity += quantity
        item.save()

        return Response({"detail": "Refund processed and stock updated successfully."}, status=status.HTTP_200_OK)

class StockTransactionViewSet(viewsets.ModelViewSet):
    """ViewSet for tracking stock transactions."""
    queryset = StockTransaction.objects.all()
    serializer_class = StockTransactionSerializer
    permission_classes = []

    def perform_create(self, serializer):
        """Override create method to apply stock transactions."""
        transaction = serializer.save()
        transaction.apply_transaction()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

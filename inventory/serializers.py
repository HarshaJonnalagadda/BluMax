from rest_framework import serializers
from .models import InventoryCategory, InventoryItem, StockTransaction

class InventoryCategorySerializer(serializers.ModelSerializer):
    """Serializer for inventory categories."""
    class Meta:
        model = InventoryCategory
        fields = ['id', 'name', 'description']

class InventoryItemSerializer(serializers.ModelSerializer):
    """Serializer for inventory items."""
    category_name = serializers.ReadOnlyField(source='category.name')  # Display category name
    is_low_stock = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = InventoryItem
        fields = ['id', 'name', 'category', 'category_name', 'quantity', 'reorder_level', 'expiry_date', 'last_updated', 'is_low_stock', 'is_expired', 'is_active']

    def get_is_low_stock(self, obj):
        """Check if stock is below reorder level."""
        return obj.check_low_stock()

    def get_is_expired(self, obj):
        """Check if item is expired."""
        return obj.check_expiry()

class StockTransactionSerializer(serializers.ModelSerializer):
    """Serializer for stock transactions."""
    item_name = serializers.ReadOnlyField(source='item.name')

    class Meta:
        model = StockTransaction
        fields = ['id', 'item', 'item_name', 'transaction_type', 'quantity', 'timestamp']

    def create(self, validated_data):
        """Override create to apply stock transaction."""
        transaction = StockTransaction.objects.create(**validated_data)
        transaction.apply_transaction()
        return transaction

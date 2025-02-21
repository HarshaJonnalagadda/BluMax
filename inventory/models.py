from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import now
from billing.models import Invoice
import uuid

class InventoryCategory(models.Model):
    """Category of inventory items (e.g., Medicine, Equipment, Supplies)"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return self.name

class InventoryItem(models.Model):
    """Inventory items including medications and medical supplies."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    category = models.ForeignKey(InventoryCategory, on_delete=models.CASCADE, related_name='items')
    quantity = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # New field for pricing
    reorder_level = models.PositiveIntegerField(default=10)
    expiry_date = models.DateField(null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)  # Flag for expired/deactivated items
    
    def check_low_stock(self):
        """Check if stock is below reorder level."""
        return self.quantity <= self.reorder_level
    
    def check_expiry(self):
        """Check if item is expired."""
        if self.expiry_date and self.expiry_date <= now().date():
            self.is_active = False
            self.save()
            return True
        return False
    
    def __str__(self):
        return f"{self.name} ({self.quantity} in stock)"

class StockTransaction(models.Model):
    """Tracks stock changes: incoming (restock) & outgoing (dispensed)."""
    class TransactionType(models.TextChoices):
        RESTOCK = 'RESTOCK', _('Restock')
        DISPENSED = 'DISPENSED', _('Dispensed')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=10, choices=TransactionType.choices)
    quantity = models.PositiveIntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def apply_transaction(self):
        """Adjust stock levels based on transaction type."""
        if self.transaction_type == self.TransactionType.RESTOCK:
            self.item.quantity += self.quantity
        elif self.transaction_type == self.TransactionType.DISPENSED:
            self.item.quantity -= self.quantity
        self.item.last_updated = now()
        self.item.save()
    
    def __str__(self):
        return f"{self.transaction_type} {self.quantity} of {self.item.name}"

class DispensedItem(models.Model):
    """Tracks medications and supplies dispensed to patients, linking them to invoices."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='dispensed_items')
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='dispensed_items')
    quantity = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    dispensed_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        """Calculate total price and update stock when a medication is dispensed."""
        self.total_price = self.item.price * self.quantity
        super().save(*args, **kwargs)
        # Record as a stock transaction
        StockTransaction.objects.create(
            item=self.item,
            transaction_type=StockTransaction.TransactionType.DISPENSED,
            quantity=self.quantity
        )
    
    def __str__(self):
        return f"{self.quantity} x {self.item.name} dispensed (Invoice: {self.invoice.id})"
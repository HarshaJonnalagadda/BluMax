from rest_framework import serializers
from .models import Invoice, Payment

class InvoiceSerializer(serializers.ModelSerializer):
    """Serializer for Invoice model."""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    total_paid = serializers.SerializerMethodField()
    balance_due = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = [
            'id', 'patient', 'appointment', 'invoice_number', 'amount', 'tax', 'total_amount', 
            'status', 'status_display', 'total_paid', 'balance_due', 'due_date', 'created_at', 'updated_at'
        ]
        read_only_fields = ['invoice_number', 'tax', 'total_amount', 'created_at', 'updated_at']
    
    def get_total_paid(self, obj):
        """Calculate total amount paid for this invoice."""
        return obj.payments.filter(status=Payment.Status.SUCCESS).aggregate(serializers.Sum('amount'))['amount__sum'] or 0
    
    def get_balance_due(self, obj):
        """Calculate the balance due on the invoice."""
        return obj.total_amount - self.get_total_paid(obj)

class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment model."""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    invoice_number = serializers.ReadOnlyField(source='invoice.invoice_number')
    
    class Meta:
        model = Payment
        fields = [
            'id', 'invoice', 'invoice_number', 'amount', 'payment_date', 'payment_method', 
            'transaction_id', 'status', 'status_display', 'metadata'
        ]
        read_only_fields = ['payment_date']

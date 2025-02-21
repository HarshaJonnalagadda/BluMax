from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum
from django.utils.timezone import now
from .models import Invoice, Payment
from .serializers import InvoiceSerializer, PaymentSerializer
from inventory.models import DispensedItem

class InvoiceViewSet(viewsets.ModelViewSet):
    """ViewSet for managing invoices."""
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer

    def create(self, request, *args, **kwargs):
        """Override create to auto-calculate tax and total amount."""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            amount = serializer.validated_data['amount']
            tax = amount * 0.18  # 18% GST
            total_amount = amount + tax
            invoice = serializer.save(tax=tax, total_amount=total_amount)
            return Response(InvoiceSerializer(invoice).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def payments(self, request, pk=None):
        """Retrieve payments associated with a specific invoice."""
        invoice = self.get_object()
        payments = Payment.objects.filter(invoice=invoice)
        serializer = PaymentSerializer(payments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def dispensed_items(self, request, pk=None):
        """Retrieve dispensed items linked to a specific invoice."""
        invoice = self.get_object()
        items = DispensedItem.objects.filter(invoice=invoice)
        return Response({"invoice_id": invoice.id, "dispensed_items": list(items.values())})

class PaymentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing payments."""
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

    def create(self, request, *args, **kwargs):
        """Process a payment and update invoice status accordingly."""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            payment = serializer.save()
            invoice = payment.invoice
            total_paid = Payment.objects.filter(invoice=invoice, status=Payment.Status.SUCCESS).aggregate(Sum('amount'))['amount__sum'] or 0
            
            if total_paid >= invoice.total_amount:
                invoice.status = Invoice.Status.PAID
            elif total_paid > 0:
                invoice.status = Invoice.Status.PARTIALLY_PAID
            invoice.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def refund(self, request, pk=None):
        """Process a refund for a payment."""
        payment = self.get_object()
        if payment.status != Payment.Status.SUCCESS:
            return Response({"error": "Only successful payments can be refunded."}, status=status.HTTP_400_BAD_REQUEST)
        
        payment.status = Payment.Status.REFUNDED
        payment.save()
        payment.invoice.update_status()
        return Response(PaymentSerializer(payment).data, status=status.HTTP_200_OK)
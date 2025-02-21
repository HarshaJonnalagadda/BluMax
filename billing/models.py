from django.db import models
from patients.models import Patient
import uuid
from django.utils.timezone import now

class Invoice(models.Model):
    """Model for storing invoice details."""
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PAID = 'PAID', 'Paid'
        CANCELLED = 'CANCELLED', 'Cancelled'
        REFUNDED = 'REFUNDED', 'Refunded'
        PARTIALLY_PAID = 'PARTIALLY_PAID', 'Partially Paid'
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    appointment = models.OneToOneField(
        "appointments.Appointment", on_delete=models.SET_NULL, null=True, blank=True, related_name="invoice_details"
    )
    invoice_number = models.CharField(max_length=20, unique=True, default=uuid.uuid4)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    due_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def update_status(self):
        """Updates the invoice status based on payments received."""
        total_paid = self.payments.filter(status=Payment.Status.SUCCESS).aggregate(models.Sum('amount'))['amount__sum'] or 0
        if total_paid >= self.total_amount:
            self.status = Invoice.Status.PAID
        elif total_paid > 0:
            self.status = Invoice.Status.PARTIALLY_PAID
        else:
            self.status = Invoice.Status.PENDING
        self.save()
    
    @staticmethod
    def generate_invoice_for_patient(patient):
        """Automatically generate an invoice when a medication is dispensed."""
        invoice, created = Invoice.objects.get_or_create(
            patient=patient,
            status=Invoice.Status.PENDING,
            defaults={"amount": 0, "tax": 0, "total_amount": 0, "due_date": now().date()}
        )
        return invoice

    @staticmethod
    def generate_invoice_for_appointment(appointment):
        """Automatically generate an invoice when an appointment is completed."""
        if not appointment.invoice:
            amount = appointment.consultation_fee if hasattr(appointment, 'consultation_fee') else 500  # Default fee
            tax = amount * 0.18  # 18% GST
            total_amount = amount + tax
            invoice = Invoice.objects.create(
                patient=appointment.patient,
                appointment=appointment,
                amount=amount,
                tax=tax,
                total_amount=total_amount,
                due_date=appointment.date
            )
            appointment.invoice = invoice
            appointment.save()
            return appointment.invoice
        return appointment.invoice
    
    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.status}"

class Payment(models.Model):
    """Model for storing payment transactions."""
    class Status(models.TextChoices):
        SUCCESS = 'SUCCESS', 'Success'
        FAILED = 'FAILED', 'Failed'
        PENDING = 'PENDING', 'Pending'
        REFUNDED = 'REFUNDED', 'Refunded'
    
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=50)
    transaction_id = models.CharField(max_length=100, unique=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    metadata = models.JSONField(default=dict)
    
    def save(self, *args, **kwargs):
        """Override save to update invoice status when payment is successful."""
        super().save(*args, **kwargs)
        if self.status == Payment.Status.SUCCESS:
            self.invoice.update_status()
    
    def __str__(self):
        return f"Payment {self.transaction_id} - {self.status}"
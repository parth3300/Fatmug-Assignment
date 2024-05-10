from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
# Create your models here.


class Vendor(models.Model):
    vendor_code = models.CharField(max_length=10, primary_key=True)
    name = models.CharField(max_length=100)
    contact_details = models.TextField()
    address = models.TextField()
    on_time_delivery_rate = models.FloatField(default=0)
    quality_rating_avg = models.FloatField(default=0)
    average_response_time = models.FloatField(default=0)
    fulfillment_rate = models.FloatField(default=0)

    def __str__(self) -> str:
        return self.name


class PurchaseOrder(models.Model):
    STATUS_CHOICE = [('pending', 'Pending'),
                     ('complete', 'Complete'),
                     ('canceled', 'Canceled')]

    po_number = models.CharField(max_length=10, primary_key=True)
    vendor = models.ForeignKey(
        Vendor, on_delete=models.CASCADE, related_name='purchase_orders')
    order_date = models.DateTimeField(auto_now_add=True)
    delivery_date = models.DateTimeField()
    items = models.JSONField()
    quantity = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICE)
    quality_rating = models.FloatField(
        null=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    issue_date = models.DateTimeField()
    acknowledgement_date = models.DateTimeField(null=True)

    def __str__(self) -> str:
        return self.po_number


class HistoricalPerformance(models.Model):
    vendor = models.ForeignKey(
        Vendor, on_delete=models.CASCADE, related_name='historical_performance')
    date = models.DateTimeField()
    on_time_delivery_rate = models.FloatField()
    quality_rating_avg = models.FloatField()
    average_response_time = models.FloatField()
    fulfillment_rate = models.FloatField()

    def __str__(self):
        return f"{self.vendor.name} - {self.date}"

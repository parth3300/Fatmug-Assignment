from rest_framework import serializers
from .models import Vendor, PurchaseOrder, HistoricalPerformance
from django.db.models import Avg, ExpressionWrapper, F, Max
from pprint import pprint
from django.utils import timezone
from datetime import timedelta


class VendorSerializer(serializers.ModelSerializer):
    on_time_delivery_rate = serializers.SerializerMethodField()
    quality_rating_avg = serializers.SerializerMethodField()
    average_response_time = serializers.SerializerMethodField()
    fulfillment_rate = serializers.SerializerMethodField()

    def get_on_time_delivery_rate(self, vendor):
        return f'{vendor.on_time_delivery_rate}%'

    def get_quality_rating_avg(self, vendor):
        return f'{vendor.quality_rating_avg}%'

    def get_average_response_time(self, vendor):
        return f'{vendor.average_response_time}'

    def get_fulfillment_rate(self, vendor):
        return f'{vendor.fulfillment_rate}%'

    class Meta:
        model = Vendor
        fields = ['vendor_code', 'name', 'contact_details', 'address',
                  'on_time_delivery_rate', 'quality_rating_avg', 'average_response_time', 'fulfillment_rate']


class CreateVendorSerializer(serializers.ModelSerializer):
    vendor_code = serializers.CharField(read_only=True)

    def create(self, validated_data):
        last_vendor = Vendor.objects.aggregate(
            max_vendor_code=Max('vendor_code'))
        last_vendor_code = last_vendor.get('max_vendor_code')

        last_code = int(last_vendor_code) + 1 if last_vendor_code else 1

        validated_data['vendor_code'] = str(last_code)
        vendor = Vendor.objects.create(**validated_data)
        HistoricalPerformance.objects.create(
            vendor=vendor,
            date=timezone.now(),
            on_time_delivery_rate=0.0,
            quality_rating_avg=0.0,
            average_response_time=0.0,
            fulfillment_rate=0.0
        )
        return vendor

    class Meta:
        model = Vendor
        fields = ['vendor_code', 'name', 'contact_details', 'address']


class PurchaseOrderSerializer(serializers.ModelSerializer):
    items = serializers.JSONField(default=dict)
    po_number = serializers.CharField(read_only=True)

    def create(self, validated_data):
        # Get the last purchase order number
        last_po = PurchaseOrder.objects.order_by('-po_number').first()
        last_po_number = int(last_po.po_number) + 1 if last_po else 1
        validated_data['po_number'] = str(last_po_number)

        # Create the purchase order
        purchase_order = PurchaseOrder.objects.create(**validated_data)

        # Retrieve the vendor associated with the purchase order
        vendor = purchase_order.vendor

        # Calculate on-time delivery rate
        completed_orders = vendor.purchase_orders.filter(
            status='complete', delivery_date__gte=F('acknowledgement_date')).count()
        total_completed_orders = vendor.purchase_orders.filter(
            status='complete').count()

        if total_completed_orders == 0:
            on_time_delivery_rate = 0
        else:
            on_time_delivery_rate = (
                completed_orders / total_completed_orders) * 100
        vendor.on_time_delivery_rate = on_time_delivery_rate

        # Calculate average quality rating
        avg_quality = vendor.purchase_orders.filter(status='complete').exclude(
            quality_rating=None).aggregate(avg_quality=Avg('quality_rating'))['avg_quality']

        if avg_quality is None:
            avg_quality = 0
        vendor.quality_rating_avg = avg_quality

        # Calculate average response time
        avg_response = vendor.purchase_orders.filter(status='complete', acknowledgement_date__isnull=False).annotate(
            response_time=F('acknowledgement_date') - F('issue_date')
        ).aggregate(avg_response=Avg('response_time'))['avg_response']

        # Check if avg_response is None and set it to 0 if so
        if avg_response is None:
            avg_response = timedelta(seconds=0)
        # Convert timedelta to seconds
        vendor.average_response_time = avg_response.total_seconds()

        # Calculate fulfillment rate
        total_orders = vendor.purchase_orders.count()
        if total_orders == 0:
            fulfillment_rate = 0
        else:
            fulfilled_orders = vendor.purchase_orders.filter(
                status='complete', quality_rating=100.0).count()
            fulfillment_rate = (fulfilled_orders / total_orders) * 100
        vendor.fulfillment_rate = fulfillment_rate

        # Save changes to the vendor
        vendor.save()

        # Create historical performance record
        HistoricalPerformance.objects.create(
            vendor=vendor,
            date=timezone.now(),
            on_time_delivery_rate=vendor.on_time_delivery_rate,
            quality_rating_avg=vendor.quality_rating_avg,
            average_response_time=vendor.average_response_time,
            fulfillment_rate=vendor.fulfillment_rate
        )

        return purchase_order

    class Meta:
        model = PurchaseOrder
        fields = ['po_number', 'vendor', 'order_date', 'delivery_date', 'items',
                  'quantity', 'status', 'quality_rating', 'issue_date', 'acknowledgement_date']


class HistoricalPerformanceSerializer(serializers.ModelSerializer):

    class Meta:
        model = HistoricalPerformance
        fields = ['id', 'vendor', 'date', 'on_time_delivery_rate',
                  'quality_rating_avg', 'average_response_time', 'fulfillment_rate']


class VendorPerformanceSerializer(serializers.Serializer):
    on_time_delivery_rate = serializers.FloatField()
    quality_rating_avg = serializers.FloatField()
    average_response_time = serializers.FloatField()
    fulfillment_rate = serializers.FloatField()


class UpdateAcknowledgmentSerializer(serializers.Serializer):
    acknowledgement_date = serializers.DateTimeField()

import imp
from django.shortcuts import redirect, render
from .models import Vendor, PurchaseOrder, HistoricalPerformance
from .serializers import VendorSerializer, CreateVendorSerializer, PurchaseOrderSerializer, HistoricalPerformanceSerializer, VendorPerformanceSerializer, UpdateAcknowledgmentSerializer
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework import generics
from django.db.models import F, Avg
from datetime import datetime
import pytz
from datetime import timedelta
from django.urls import reverse
from django.http import HttpResponse



# Create your views here.


class VendorViewSet(ModelViewSet):
    queryset = Vendor.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateVendorSerializer
        return VendorSerializer


class PurchaseOrderViewSet(ModelViewSet):
    queryset = PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializer


class HistoricalPerformanceViewSet(ReadOnlyModelViewSet):
    queryset = HistoricalPerformance.objects.all()
    serializer_class = HistoricalPerformanceSerializer


class VendorPerformanceAPIView(generics.RetrieveAPIView):
    serializer_class = VendorPerformanceSerializer

    def retrieve(self, request, *args, **kwargs):
        # find the vendor with vendor code
        vendor_code = self.kwargs.get('vendor_code')
        vendor = get_object_or_404(Vendor, vendor_code=vendor_code)
        on_time_delivery_rate = vendor.on_time_delivery_rate
        quality_rating_avg = vendor.quality_rating_avg
        average_response_time = vendor.average_response_time
        fulfillment_rate = vendor.fulfillment_rate

        # Serialize the data
        serializer = self.get_serializer(data={
            'on_time_delivery_rate': on_time_delivery_rate,
            'quality_rating_avg': quality_rating_avg,
            'average_response_time': average_response_time,
            'fulfillment_rate': fulfillment_rate
        })
        serializer.is_valid(raise_exception=True)

        return Response(serializer.data)

from django.urls import reverse

class UpdateAcknowledgmentView(generics.UpdateAPIView):
    serializer_class = UpdateAcknowledgmentSerializer

    def update(self, request, *args, **kwargs):
        # Find purchase_order object
        po_number = self.kwargs.get('po_number')
        po = get_object_or_404(PurchaseOrder, po_number=po_number)

        # Update acknowledgment_date
        # Store the old acknowledgement date
        new_acknowledgement_date = request.data.get('acknowledgement_date')
        po.acknowledgement_date = new_acknowledgement_date
        po.save()

        # Trigger the calculation for average_response_time
        vendor = po.vendor
        avg_response = vendor.purchase_orders.filter(status='complete', acknowledgement_date__isnull=False).annotate(
            response_time=F('acknowledgement_date') - F('issue_date')
        ).aggregate(avg_response=Avg('response_time'))['avg_response']

        # Check if avg_response is None and set it to 0 if so
        if avg_response is None:
            avg_response = timedelta(seconds=0)
        # Convert timedelta to seconds
        vendor.average_response_time = avg_response.total_seconds()
        vendor.save()

        # Redirect to the detail view of the updated purchase order
        return HttpResponse("Record updated successfully", status=200)


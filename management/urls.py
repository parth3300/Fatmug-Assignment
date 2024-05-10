from django.urls import path, include
from . import views
from rest_framework import routers

router = routers.DefaultRouter()
router.register('vendors', views.VendorViewSet)
router.register('purchaseorders', views.PurchaseOrderViewSet)
router.register('historicalperformances', views.HistoricalPerformanceViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('vendors/<int:vendor_code>/performance/', views.VendorPerformanceAPIView.as_view(), name='vendor_performance'),
    path('purchaseorders/<int:po_number>/acknowledge/', views.UpdateAcknowledgmentView.as_view(), name='update_acknowledgment')
]

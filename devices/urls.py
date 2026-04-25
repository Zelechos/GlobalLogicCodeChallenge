from django.urls import path
from .views import (
    DeviceListCreateView,
    DeviceDetailView,
    update_device_last_seen,
    device_statistics_view,
)

urlpatterns = [
    # Device management
    path('', DeviceListCreateView.as_view(), name='device-list-create'),
    path('<int:pk>/', DeviceDetailView.as_view(), name='device-detail'),
    path('<int:device_id>/update-last-seen/', update_device_last_seen, name='update-last-seen'),
    path('statistics/', device_statistics_view, name='device-statistics'),
]

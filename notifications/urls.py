from django.urls import path
from .views import (
    NotificationListView,
    NotificationDetailView,
    mark_notification_read,
    unread_notifications_count,
)

urlpatterns = [
    # Notification management
    path('', NotificationListView.as_view(), name='notification-list'),
    path('<int:pk>/', NotificationDetailView.as_view(), name='notification-detail'),
    path('<int:pk>/mark-read/', mark_notification_read, name='mark-notification-read'),
    path('unread-count/', unread_notifications_count, name='unread-count'),
]

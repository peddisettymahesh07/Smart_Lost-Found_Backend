from django.urls import path
from .views import (
    ClaimRequestListCreateView,
    ClaimRequestDetailView,
    ClaimStatusUpdateView,
)

urlpatterns = [
    path('', ClaimRequestListCreateView.as_view(), name='claim_list_create'),
    path('<int:pk>/', ClaimRequestDetailView.as_view(), name='claim_detail'),
    path('<int:pk>/status/', ClaimStatusUpdateView.as_view(), name='claim_status_update'),
]

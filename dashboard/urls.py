from django.urls import path
from .views import AdminDashboardStatsView, UserDashboardStatsView

urlpatterns = [
    path('stats/', AdminDashboardStatsView.as_view(), name='admin_dashboard_stats'),
    path('user-stats/', UserDashboardStatsView.as_view(), name='user_dashboard_stats'),
]

from django.urls import path
from .views import LocationListView, NearbyItemsView

urlpatterns = [
    path('', LocationListView.as_view(), name='location_list'),
    path('nearby/', NearbyItemsView.as_view(), name='nearby_items'),
]

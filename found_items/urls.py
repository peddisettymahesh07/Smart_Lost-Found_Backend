from django.urls import path
from .views import FoundItemListCreateView, FoundItemDetailView

urlpatterns = [
    path('', FoundItemListCreateView.as_view(), name='found_item_list_create'),
    path('<int:pk>/', FoundItemDetailView.as_view(), name='found_item_detail'),
]

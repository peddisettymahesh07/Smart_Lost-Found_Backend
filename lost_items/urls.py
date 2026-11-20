from django.urls import path
from .views import LostItemListCreateView, LostItemDetailView

urlpatterns = [
    path('', LostItemListCreateView.as_view(), name='lost_item_list_create'),
    path('<int:pk>/', LostItemDetailView.as_view(), name='lost_item_detail'),
]

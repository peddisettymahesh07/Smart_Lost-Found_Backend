from django.urls import path
from .views import (
    MatchRecordListView,
    MatchRecordDetailView,
    MatchRespondView,
    MatchGenerateView,
)

urlpatterns = [
    path('', MatchRecordListView.as_view(), name='match_list'),
    path('generate/', MatchGenerateView.as_view(), name='match_generate'),
    path('<int:pk>/', MatchRecordDetailView.as_view(), name='match_detail'),
    path('<int:pk>/respond/', MatchRespondView.as_view(), name='match_respond'),
]

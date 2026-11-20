from rest_framework import views, permissions, status
from rest_framework.response import Response
from django.db.models import Count, Q
from accounts.models import User
from lost_items.models import LostItem
from found_items.models import FoundItem
from matching.models import MatchRecord
from claims.models import ClaimRequest
from .models import AdminAction
from accounts.permissions import IsAdministrator


class AdminDashboardStatsView(views.APIView):
    permission_classes = [IsAdministrator]

    def get(self, request):
        total_users = User.objects.count()
        total_lost = LostItem.objects.count()
        total_found = FoundItem.objects.count()
        total_matches = MatchRecord.objects.count()
        high_confidence_matches = MatchRecord.objects.filter(confidence_level='High').count()
        pending_claims = ClaimRequest.objects.filter(status='pending').count()
        resolved_cases = ClaimRequest.objects.filter(status='approved').count()
        rejected_claims = ClaimRequest.objects.filter(status='rejected').count()

        # Category Breakdown
        lost_categories = list(LostItem.objects.values('category').annotate(count=Count('id')).order_by('-count'))
        found_categories = list(FoundItem.objects.values('category').annotate(count=Count('id')).order_by('-count'))

        # Combine category counts
        category_map = {}
        for item in lost_categories:
            category_map[item['category']] = category_map.get(item['category'], 0) + item['count']
        for item in found_categories:
            category_map[item['category']] = category_map.get(item['category'], 0) + item['count']

        category_breakdown = [{'category': cat, 'count': cnt} for cat, cnt in sorted(category_map.items(), key=lambda x: x[1], reverse=True)]

        # Confidence distribution
        confidence_distribution = {
            'High': MatchRecord.objects.filter(confidence_level='High').count(),
            'Medium': MatchRecord.objects.filter(confidence_level='Medium').count(),
            'Low': MatchRecord.objects.filter(confidence_level='Low').count(),
        }

        # City distribution
        city_counts = list(FoundItem.objects.values('city').annotate(count=Count('id')).order_by('-count')[:8])

        # Recent activities
        recent_lost = list(LostItem.objects.select_related('user').order_by('-created_at')[:5].values(
            'id', 'title', 'category', 'city', 'status', 'created_at', 'user__full_name'
        ))
        recent_found = list(FoundItem.objects.select_related('user').order_by('-created_at')[:5].values(
            'id', 'title', 'category', 'city', 'status', 'created_at', 'user__full_name'
        ))
        recent_claims = list(ClaimRequest.objects.select_related('claimant', 'found_item').order_by('-created_at')[:5].values(
            'id', 'found_item_id', 'found_item__title', 'claimant__full_name', 'status', 'created_at'
        ))
        recent_actions = list(AdminAction.objects.select_related('admin').order_by('-created_at')[:8].values(
            'id', 'action', 'target_type', 'target_id', 'details', 'created_at', 'admin__email'
        ))

        return Response({
            'summary': {
                'total_users': total_users,
                'total_lost_items': total_lost,
                'total_found_items': total_found,
                'total_matches': total_matches,
                'high_confidence_matches': high_confidence_matches,
                'pending_claims': pending_claims,
                'resolved_cases': resolved_cases,
                'rejected_claims': rejected_claims,
            },
            'category_breakdown': category_breakdown,
            'confidence_distribution': confidence_distribution,
            'city_distribution': city_counts,
            'recent_lost': recent_lost,
            'recent_found': recent_found,
            'recent_claims': recent_claims,
            'recent_actions': recent_actions,
        })


class UserDashboardStatsView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        my_lost_count = LostItem.objects.filter(user=user).count()
        my_found_count = FoundItem.objects.filter(user=user).count()
        my_matches_count = MatchRecord.objects.filter(
            Q(lost_item__user=user) | Q(found_item__user=user)
        ).count()
        my_claims_count = ClaimRequest.objects.filter(claimant=user).count()
        pending_received_claims = ClaimRequest.objects.filter(found_item__user=user, status='pending').count()

        return Response({
            'my_lost_count': my_lost_count,
            'my_found_count': my_found_count,
            'my_matches_count': my_matches_count,
            'my_claims_count': my_claims_count,
            'pending_received_claims': pending_received_claims,
        })

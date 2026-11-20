from rest_framework import generics, permissions, status, views
from rest_framework.response import Response
from .models import MatchRecord
from .serializers import MatchRecordSerializer
from .services import run_global_matching, run_matching_for_lost_item, run_matching_for_found_item
from lost_items.models import LostItem
from found_items.models import FoundItem
from accounts.permissions import IsAdministrator


class MatchRecordListView(generics.ListAPIView):
    serializer_class = MatchRecordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = MatchRecord.objects.all().select_related(
            'lost_item', 'found_item', 'lost_item__user', 'found_item__user'
        ).prefetch_related(
            'lost_item__images', 'found_item__images'
        ).order_by('-combined_score')

        # Role filter: regular users only see matches relating to their items, admins see all
        if not (user.role == 'admin' or user.is_staff or user.is_superuser):
            queryset = queryset.filter(
                models_Q := (
                    generics.models.Q(lost_item__user=user) | generics.models.Q(found_item__user=user)
                )
            )

        lost_item_id = self.request.query_params.get('lost_item_id')
        found_item_id = self.request.query_params.get('found_item_id')
        confidence = self.request.query_params.get('confidence')
        status_param = self.request.query_params.get('status')
        min_score = self.request.query_params.get('min_score')

        if lost_item_id:
            queryset = queryset.filter(lost_item_id=lost_item_id)
        if found_item_id:
            queryset = queryset.filter(found_item_id=found_item_id)
        if confidence:
            queryset = queryset.filter(confidence_level__iexact=confidence)
        if status_param:
            queryset = queryset.filter(status=status_param)
        if min_score:
            try:
                queryset = queryset.filter(combined_score__gte=float(min_score))
            except ValueError:
                pass

        return queryset


class MatchRecordDetailView(generics.RetrieveAPIView):
    serializer_class = MatchRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = MatchRecord.objects.all().select_related(
        'lost_item', 'found_item', 'lost_item__user', 'found_item__user'
    ).prefetch_related('lost_item__images', 'found_item__images')


class MatchRespondView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            match = MatchRecord.objects.get(pk=pk)
        except MatchRecord.DoesNotExist:
            return Response({'error': 'Match not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Check permission: user must be lost_item owner, found_item owner, or admin
        user = request.user
        if not (user == match.lost_item.user or user == match.found_item.user or user.role == 'admin' or user.is_staff):
            return Response({'error': 'You do not have permission to respond to this match.'}, status=status.HTTP_403_FORBIDDEN)

        new_status = request.data.get('status')
        allowed_statuses = ['reviewed', 'confirmed_match', 'rejected', 'claim_submitted']
        if new_status not in allowed_statuses:
            return Response({'error': f'Invalid status. Allowed values: {allowed_statuses}'}, status=status.HTTP_400_BAD_REQUEST)

        match.status = new_status
        match.save(update_fields=['status', 'updated_at'])
        return Response({'message': f'Match status updated to {new_status}.', 'match': MatchRecordSerializer(match).data})


class MatchGenerateView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        lost_id = request.data.get('lost_item_id')
        found_id = request.data.get('found_item_id')

        if lost_id:
            try:
                lost_item = LostItem.objects.get(pk=lost_id)
                matches = run_matching_for_lost_item(lost_item)
                return Response({
                    'message': f'AI matching completed for lost item #{lost_id}.',
                    'count': len(matches),
                    'matches': MatchRecordSerializer(matches, many=True).data
                })
            except LostItem.DoesNotExist:
                return Response({'error': 'Lost item not found.'}, status=status.HTTP_404_NOT_FOUND)

        elif found_id:
            try:
                found_item = FoundItem.objects.get(pk=found_id)
                matches = run_matching_for_found_item(found_item)
                return Response({
                    'message': f'AI matching completed for found item #{found_id}.',
                    'count': len(matches),
                    'matches': MatchRecordSerializer(matches, many=True).data
                })
            except FoundItem.DoesNotExist:
                return Response({'error': 'Found item not found.'}, status=status.HTTP_404_NOT_FOUND)

        else:
            # Batch trigger all
            matches = run_global_matching()
            return Response({
                'message': 'Global AI matching completed across all active items.',
                'matches_evaluated': len(matches)
            })

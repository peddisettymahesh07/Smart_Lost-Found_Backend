from django.utils import timezone
from rest_framework import generics, permissions, status, views
from rest_framework.response import Response
from django.db.models import Q
from .models import ClaimRequest
from .serializers import ClaimRequestSerializer
from notifications.services import create_notification
from dashboard.models import AdminAction
from accounts.models import User


class ClaimRequestListCreateView(generics.ListCreateAPIView):
    serializer_class = ClaimRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Admins see all claims
        if user.role == 'admin' or user.is_staff or user.is_superuser:
            return ClaimRequest.objects.all().select_related('found_item', 'lost_item', 'claimant', 'reviewed_by').order_by('-created_at')

        # Regular users/finders see claims they submitted or claims submitted on items they found
        return ClaimRequest.objects.filter(
            Q(claimant=user) | Q(found_item__user=user)
        ).select_related('found_item', 'lost_item', 'claimant', 'reviewed_by').order_by('-created_at')

    def perform_create(self, serializer):
        claim = serializer.save(claimant=self.request.user)

        # Notify the item finder
        finder = claim.found_item.user
        create_notification(
            user=finder,
            title=f"New Ownership Claim on '{claim.found_item.title}'",
            message=f"{self.request.user.full_name} has submitted an ownership claim for your found item '{claim.found_item.title}'. Please review the verification answers.",
            notification_type='claim_submitted',
            related_item_type='claim',
            related_item_id=claim.id
        )

        # Notify administrators
        admins = User.objects.filter(Q(role='admin') | Q(is_superuser=True))
        for admin in admins:
            create_notification(
                user=admin,
                title=f"New Claim Submitted for Found Item #{claim.found_item_id}",
                message=f"Claim #{claim.id} submitted by {self.request.user.email} on item '{claim.found_item.title}'.",
                notification_type='claim_submitted',
                related_item_type='claim',
                related_item_id=claim.id,
                send_email_alert=False
            )


class ClaimRequestDetailView(generics.RetrieveAPIView):
    serializer_class = ClaimRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin' or user.is_staff or user.is_superuser:
            return ClaimRequest.objects.all()
        return ClaimRequest.objects.filter(Q(claimant=user) | Q(found_item__user=user))


class ClaimStatusUpdateView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        try:
            claim = ClaimRequest.objects.select_related('found_item', 'lost_item', 'claimant').get(pk=pk)
        except ClaimRequest.DoesNotExist:
            return Response({'error': 'Claim request not found.'}, status=status.HTTP_404_NOT_FOUND)

        user = request.user
        is_admin = (user.role == 'admin' or user.is_staff or user.is_superuser)
        is_finder = (user == claim.found_item.user)

        if not (is_admin or is_finder):
            return Response({'error': 'You do not have permission to review or change this claim status.'}, status=status.HTTP_403_FORBIDDEN)

        new_status = request.data.get('status')
        finder_response = request.data.get('finder_response')
        admin_notes = request.data.get('admin_notes')

        if new_status and new_status not in ['pending', 'under_review', 'approved', 'rejected']:
            return Response({'error': 'Invalid status choice.'}, status=status.HTTP_400_BAD_REQUEST)

        if finder_response:
            claim.finder_response = finder_response

        if is_admin and admin_notes:
            claim.admin_notes = admin_notes

        if new_status:
            claim.status = new_status
            claim.reviewed_by = user
            claim.reviewed_at = timezone.now()

            # If claim is approved, update items status
            if new_status == 'approved':
                claim.found_item.status = 'claimed'
                claim.found_item.save(update_fields=['status'])
                if claim.lost_item:
                    claim.lost_item.status = 'claimed'
                    claim.lost_item.save(update_fields=['status'])

                create_notification(
                    user=claim.claimant,
                    title=f"Claim Approved for '{claim.found_item.title}'!",
                    message=f"Congratulations! Your ownership claim on '{claim.found_item.title}' has been verified and approved. Coordinate retrieval with the finder.",
                    notification_type='claim_approved',
                    related_item_type='claim',
                    related_item_id=claim.id
                )

            elif new_status == 'rejected':
                create_notification(
                    user=claim.claimant,
                    title=f"Claim Update for '{claim.found_item.title}'",
                    message=f"Your claim for '{claim.found_item.title}' was reviewed and rejected. Additional proof may be required.",
                    notification_type='claim_rejected',
                    related_item_type='claim',
                    related_item_id=claim.id
                )

        claim.save()

        # Audit admin action if action taken by admin
        if is_admin:
            AdminAction.objects.create(
                admin=user,
                action=f"claim_{new_status or 'updated'}",
                target_type='ClaimRequest',
                target_id=claim.id,
                details=f"Status set to {new_status}. Notes: {admin_notes or finder_response or 'N/A'}"
            )

        return Response({
            'message': f'Claim #{claim.id} updated successfully.',
            'claim': ClaimRequestSerializer(claim, context={'request': request}).data
        })

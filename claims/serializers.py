from rest_framework import serializers
from .models import ClaimRequest
from found_items.serializers import FoundItemSerializer
from lost_items.serializers import LostItemSerializer


class ClaimRequestSerializer(serializers.ModelSerializer):
    claimant_name = serializers.ReadOnlyField(source='claimant.full_name')
    claimant_email = serializers.ReadOnlyField(source='claimant.email')
    found_item_title = serializers.ReadOnlyField(source='found_item.title')
    found_item_category = serializers.ReadOnlyField(source='found_item.category')
    found_item_city = serializers.ReadOnlyField(source='found_item.city')
    finder_name = serializers.ReadOnlyField(source='found_item.user.full_name')
    finder_email = serializers.ReadOnlyField(source='found_item.user.email')
    proof_document = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = ClaimRequest
        fields = (
            'id', 'found_item', 'found_item_title', 'found_item_category', 'found_item_city',
            'lost_item', 'claimant', 'claimant_name', 'claimant_email',
            'proof_description', 'secret_identifiers', 'proof_document',
            'status', 'finder_response', 'admin_notes', 'reviewed_by', 'reviewed_at',
            'finder_name', 'finder_email', 'created_at', 'updated_at'
        )
        read_only_fields = (
            'id', 'claimant', 'reviewed_by', 'reviewed_at', 'created_at', 'updated_at'
        )

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        request = self.context.get('request')
        # Security protection: hide private proof info if user is not claimant, item finder, or admin
        if request and request.user.is_authenticated:
            user = request.user
            is_claimant = (user == instance.claimant)
            is_finder = (user == instance.found_item.user)
            is_admin = (user.role == 'admin' or user.is_staff or user.is_superuser)

            if not (is_claimant or is_finder or is_admin):
                ret['proof_description'] = "[RESTRICTED - Confidential Verification Details]"
                ret['secret_identifiers'] = "[RESTRICTED]"
                ret['proof_document'] = None
        else:
            ret['proof_description'] = "[RESTRICTED]"
            ret['secret_identifiers'] = "[RESTRICTED]"
            ret['proof_document'] = None

        return ret

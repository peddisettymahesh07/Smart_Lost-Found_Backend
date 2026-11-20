from rest_framework import serializers
from .models import MatchRecord, ItemImage
from lost_items.serializers import LostItemSerializer
from found_items.serializers import FoundItemSerializer


class MatchRecordSerializer(serializers.ModelSerializer):
    lost_item = LostItemSerializer(read_only=True)
    found_item = FoundItemSerializer(read_only=True)
    lost_item_id = serializers.IntegerField(write_only=True, required=False)
    found_item_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = MatchRecord
        fields = (
            'id', 'lost_item', 'found_item', 'lost_item_id', 'found_item_id',
            'image_similarity', 'category_similarity', 'colour_similarity',
            'description_similarity', 'location_similarity', 'date_similarity',
            'combined_score', 'confidence_level', 'distance_km', 'status',
            'explanation', 'created_at', 'updated_at'
        )
        read_only_fields = (
            'id', 'image_similarity', 'category_similarity', 'colour_similarity',
            'description_similarity', 'location_similarity', 'date_similarity',
            'combined_score', 'confidence_level', 'distance_km', 'created_at', 'updated_at'
        )

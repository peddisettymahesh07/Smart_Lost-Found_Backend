from rest_framework import serializers
from .models import Location


class LocationSerializer(serializers.ModelSerializer):
    distance_km = serializers.FloatField(read_only=True, required=False)
    item_title = serializers.SerializerMethodField()
    item_category = serializers.SerializerMethodField()
    item_colour = serializers.SerializerMethodField()
    item_image = serializers.SerializerMethodField()

    class Meta:
        model = Location
        fields = (
            'id', 'item_type', 'item_id', 'latitude', 'longitude', 'area', 'city',
            'created_at', 'distance_km', 'item_title', 'item_category', 'item_colour', 'item_image'
        )

    def get_item_title(self, obj):
        from lost_items.models import LostItem
        from found_items.models import FoundItem
        if obj.item_type == 'lost':
            item = LostItem.objects.filter(id=obj.item_id).first()
            return item.title if item else 'Lost Item'
        else:
            item = FoundItem.objects.filter(id=obj.item_id).first()
            return item.title if item else 'Found Item'

    def get_item_category(self, obj):
        from lost_items.models import LostItem
        from found_items.models import FoundItem
        if obj.item_type == 'lost':
            item = LostItem.objects.filter(id=obj.item_id).first()
            return item.category if item else 'Other'
        else:
            item = FoundItem.objects.filter(id=obj.item_id).first()
            return item.category if item else 'Other'

    def get_item_colour(self, obj):
        from lost_items.models import LostItem
        from found_items.models import FoundItem
        if obj.item_type == 'lost':
            item = LostItem.objects.filter(id=obj.item_id).first()
            return item.colour if item else 'Other'
        else:
            item = FoundItem.objects.filter(id=obj.item_id).first()
            return item.colour if item else 'Other'

    def get_item_image(self, obj):
        from lost_items.models import LostItem
        from found_items.models import FoundItem
        if obj.item_type == 'lost':
            item = LostItem.objects.filter(id=obj.item_id).first()
            return item.primary_image if item else None
        else:
            item = FoundItem.objects.filter(id=obj.item_id).first()
            return item.primary_image if item else None

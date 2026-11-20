from rest_framework import serializers
from .models import FoundItem
from matching.models import ItemImage


class FoundItemSerializer(serializers.ModelSerializer):
    user_name = serializers.ReadOnlyField(source='user.full_name')
    user_email = serializers.ReadOnlyField(source='user.email')
    images = serializers.SerializerMethodField()
    image = serializers.ImageField(write_only=True, required=False)

    class Meta:
        model = FoundItem
        fields = (
            'id', 'user', 'user_name', 'user_email', 'title', 'category', 'description',
            'colour', 'date_found', 'location_area', 'city', 'latitude', 'longitude',
            'status', 'images', 'image', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'user', 'created_at', 'updated_at')

    def create(self, validated_data):
        validated_data.pop('image', None)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data.pop('image', None)
        return super().update(instance, validated_data)

    def get_images(self, obj):
        return [
            {'id': img.id, 'image': img.image.url if img.image else None, 'is_primary': img.is_primary}
            for img in obj.images.all()
        ]

    def validate_latitude(self, value):
        if value is not None and not (-90.0 <= float(value) <= 90.0):
            raise serializers.ValidationError("Latitude must be between -90 and 90.")
        return value

    def validate_longitude(self, value):
        if value is not None and not (-180.0 <= float(value) <= 180.0):
            raise serializers.ValidationError("Longitude must be between -180 and 180.")
        return value

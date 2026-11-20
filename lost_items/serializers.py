from rest_framework import serializers
from .models import LostItem
from matching.models import ItemImage


class ItemImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemImage
        fields = ('id', 'image', 'is_primary', 'created_at')


class LostItemSerializer(serializers.ModelSerializer):
    user_name = serializers.ReadOnlyField(source='user.full_name')
    user_email = serializers.ReadOnlyField(source='user.email')
    images = ItemImageSerializer(many=True, read_only=True)
    image = serializers.ImageField(write_only=True, required=False)

    class Meta:
        model = LostItem
        fields = (
            'id', 'user', 'user_name', 'user_email', 'title', 'category', 'description',
            'colour', 'date_lost', 'location_area', 'city', 'latitude', 'longitude',
            'contact_preference', 'status', 'images', 'image', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'user', 'created_at', 'updated_at')

    def create(self, validated_data):
        validated_data.pop('image', None)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data.pop('image', None)
        return super().update(instance, validated_data)

    def validate_latitude(self, value):
        if value is not None and not (-90.0 <= float(value) <= 90.0):
            raise serializers.ValidationError("Latitude must be between -90 and 90.")
        return value

    def validate_longitude(self, value):
        if value is not None and not (-180.0 <= float(value) <= 180.0):
            raise serializers.ValidationError("Longitude must be between -180 and 180.")
        return value

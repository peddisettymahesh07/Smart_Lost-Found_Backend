from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'full_name', 'email', 'phone_number', 'role', 'password', 'confirm_password')
        extra_kwargs = {
            'role': {'required': False},
            'phone_number': {'required': False},
        }

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email address already exists.")
        return value.lower()

    def validate(self, data):
        if data.get('password') != data.get('confirm_password'):
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        # Basic password strength validation
        password = data.get('password')
        if not any(c.isdigit() for c in password):
            raise serializers.ValidationError({"password": "Password must contain at least one digit."})
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        role = validated_data.get('role', 'user')
        user = User.objects.create_user(password=password, **validated_data)
        if role == 'admin':
            user.is_staff = True
            user.save(update_fields=['is_staff'])
        return user


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email', '').strip().lower()
        password = data.get('password')

        if not email or not password:
            raise serializers.ValidationError("Both email and password are required.")

        user = authenticate(email=email, password=password)
        if not user:
            raise serializers.ValidationError("Invalid email or password.")
        if not user.is_active:
            raise serializers.ValidationError("This user account is inactive or disabled.")

        refresh = RefreshToken.for_user(user)
        return {
            'user': user,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'full_name', 'email', 'phone_number', 'role', 'profile_image', 'created_at')
        read_only_fields = ('id', 'email', 'role', 'created_at')


class UserAdminSerializer(serializers.ModelSerializer):
    report_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'full_name', 'email', 'phone_number', 'role', 'is_active', 'is_staff', 'created_at', 'report_count')

    def get_report_count(self, obj):
        lost_count = getattr(obj, 'lost_items_count', 0) if hasattr(obj, 'lost_items_count') else obj.lost_items.count()
        found_count = getattr(obj, 'found_items_count', 0) if hasattr(obj, 'found_items_count') else obj.found_items.count()
        return {'lost': lost_count, 'found': found_count}

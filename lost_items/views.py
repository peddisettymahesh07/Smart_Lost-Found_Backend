from rest_framework import generics, permissions, filters, status
from rest_framework.response import Response
from django.db.models import Q
from .models import LostItem
from .serializers import LostItemSerializer
from accounts.permissions import IsOwnerOrAdmin
from matching.models import ItemImage
from matching.ai_engine import extract_image_embedding
from matching.services import run_matching_for_lost_item
from locations.models import Location


class LostItemListCreateView(generics.ListCreateAPIView):
    serializer_class = LostItemSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'city', 'location_area']
    ordering_fields = ['created_at', 'date_lost', 'title']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = LostItem.objects.all().prefetch_related('images').select_related('user')
        category = self.request.query_params.get('category')
        city = self.request.query_params.get('city')
        colour = self.request.query_params.get('colour')
        status_param = self.request.query_params.get('status')
        my_items = self.request.query_params.get('my_items')

        if category:
            queryset = queryset.filter(category__iexact=category)
        if city:
            queryset = queryset.filter(city__icontains=city)
        if colour:
            queryset = queryset.filter(colour__iexact=colour)
        if status_param:
            queryset = queryset.filter(status=status_param)
        if my_items and self.request.user.is_authenticated:
            queryset = queryset.filter(user=self.request.user)

        return queryset

    def perform_create(self, serializer):
        image_file = self.request.FILES.get('image')
        lost_item = serializer.save(user=self.request.user)

        if image_file:
            # Generate real AI image embedding
            embedding = extract_image_embedding(image_file)
            image_file.seek(0)
            ItemImage.objects.create(
                lost_item=lost_item,
                image=image_file,
                embedding=embedding,
                is_primary=True
            )

        # Sync location if coordinates provided
        if lost_item.latitude and lost_item.longitude:
            Location.objects.create(
                item_type='lost',
                item_id=lost_item.id,
                latitude=lost_item.latitude,
                longitude=lost_item.longitude,
                area=lost_item.location_area,
                city=lost_item.city
            )

        # Trigger AI matching against existing found items
        try:
            run_matching_for_lost_item(lost_item)
        except Exception:
            pass


class LostItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = LostItem.objects.all().prefetch_related('images').select_related('user')
    serializer_class = LostItemSerializer

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsOwnerOrAdmin()]

    def perform_update(self, serializer):
        image_file = self.request.FILES.get('image')
        lost_item = serializer.save()

        if image_file:
            embedding = extract_image_embedding(image_file)
            image_file.seek(0)
            ItemImage.objects.create(
                lost_item=lost_item,
                image=image_file,
                embedding=embedding,
                is_primary=True
            )

        if lost_item.latitude and lost_item.longitude:
            Location.objects.update_or_create(
                item_type='lost',
                item_id=lost_item.id,
                defaults={
                    'latitude': lost_item.latitude,
                    'longitude': lost_item.longitude,
                    'area': lost_item.location_area,
                    'city': lost_item.city,
                }
            )

        # Re-run AI matching
        try:
            run_matching_for_lost_item(lost_item)
        except Exception:
            pass

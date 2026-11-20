from rest_framework import views, permissions, status
from rest_framework.response import Response
from .models import Location, calculate_haversine_distance
from .serializers import LocationSerializer


class LocationListView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        queryset = Location.objects.all().order_by('-created_at')
        item_type = request.query_params.get('item_type')
        city = request.query_params.get('city')

        if item_type in ['lost', 'found']:
            queryset = queryset.filter(item_type=item_type)
        if city:
            queryset = queryset.filter(city__icontains=city)

        serializer = LocationSerializer(queryset[:100], many=True)
        return Response(serializer.data)


class NearbyItemsView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        lat_str = request.query_params.get('lat')
        lon_str = request.query_params.get('lon')
        radius_km = float(request.query_params.get('radius_km', 25.0))
        item_type = request.query_params.get('item_type', 'all')
        city = request.query_params.get('city')
        category = request.query_params.get('category')

        if not lat_str or not lon_str:
            # If no coordinates given, return items in city or all recent items
            queryset = Location.objects.all().order_by('-created_at')
            if item_type in ['lost', 'found']:
                queryset = queryset.filter(item_type=item_type)
            if city:
                queryset = queryset.filter(city__icontains=city)
            serializer = LocationSerializer(queryset[:50], many=True)
            return Response({'results': serializer.data, 'radius_km': radius_km})

        try:
            target_lat = float(lat_str)
            target_lon = float(lon_str)
        except ValueError:
            return Response({'error': 'Invalid latitude or longitude coordinates.'}, status=status.HTTP_400_BAD_REQUEST)

        locations = Location.objects.all()
        if item_type in ['lost', 'found']:
            locations = locations.filter(item_type=item_type)
        if city:
            locations = locations.filter(city__icontains=city)

        nearby_results = []
        for loc in locations:
            dist = calculate_haversine_distance(target_lat, target_lon, loc.latitude, loc.longitude)
            if dist is not None and dist <= radius_km:
                loc.distance_km = dist
                nearby_results.append(loc)

        # Sort by distance
        nearby_results.sort(key=lambda x: getattr(x, 'distance_km', 999999))

        serializer = LocationSerializer(nearby_results[:50], many=True)
        return Response({
            'count': len(nearby_results),
            'radius_km': radius_km,
            'origin': {'latitude': target_lat, 'longitude': target_lon},
            'results': serializer.data
        })

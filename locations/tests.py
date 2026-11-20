from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from locations.models import Location, calculate_haversine_distance


class LocationNearbyTestCase(APITestCase):
    def setUp(self):
        # Create sample locations in Manhattan, NY
        self.loc_times_square = Location.objects.create(
            item_type='lost',
            item_id=101,
            latitude=40.758896,
            longitude=-73.985130,
            area='Times Square Broadway',
            city='New York'
        )
        self.loc_central_park = Location.objects.create(
            item_type='found',
            item_id=202,
            latitude=40.785091,
            longitude=-73.968285,
            area='Central Park Great Lawn',
            city='New York'
        )
        # Location in Philadelphia (~130 km away)
        self.loc_philly = Location.objects.create(
            item_type='found',
            item_id=303,
            latitude=39.952583,
            longitude=-75.165222,
            area='City Hall',
            city='Philadelphia'
        )

    def test_haversine_distance_calculation(self):
        # Times Square to Central Park is approx 3.2 - 3.5 km
        dist = calculate_haversine_distance(
            self.loc_times_square.latitude, self.loc_times_square.longitude,
            self.loc_central_park.latitude, self.loc_central_park.longitude
        )
        self.assertIsNotNone(dist)
        self.assertTrue(2.8 <= dist <= 3.8)

    def test_nearby_api_with_radius(self):
        url = reverse('nearby_items')
        # Search from Times Square within 10 km
        response = self.client.get(url, {
            'lat': 40.758896,
            'lon': -73.985130,
            'radius_km': 10.0,
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item['item_id'] for item in response.data['results']]
        self.assertIn(101, ids)
        self.assertIn(202, ids)
        self.assertNotIn(303, ids)  # Philly should be excluded

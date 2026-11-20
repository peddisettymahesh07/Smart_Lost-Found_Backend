import math
from django.db import models


def calculate_haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points
    on the earth in kilometers using the Haversine formula.
    """
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return None

    try:
        lat1, lon1, lat2, lon2 = float(lat1), float(lon1), float(lat2), float(lon2)
    except (ValueError, TypeError):
        return None

    # Radius of earth in kilometers
    r = 6371.0

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    distance = r * c
    return round(distance, 2)


class Location(models.Model):
    ITEM_TYPE_CHOICES = (
        ('lost', 'Lost Item'),
        ('found', 'Found Item'),
    )

    item_type = models.CharField(max_length=10, choices=ITEM_TYPE_CHOICES, db_index=True)
    item_id = models.PositiveIntegerField(db_index=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=7)
    longitude = models.DecimalField(max_digits=10, decimal_places=7)
    area = models.CharField(max_length=255)
    city = models.CharField(max_length=100, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'locations'
        verbose_name = 'Location'
        verbose_name_plural = 'Locations'
        indexes = [
            models.Index(fields=['city', 'item_type']),
            models.Index(fields=['latitude', 'longitude']),
        ]

    def __str__(self):
        return f"{self.item_type.upper()} #{self.item_id} @ {self.area}, {self.city} ({self.latitude}, {self.longitude})"

    def distance_to(self, lat, lon):
        return calculate_haversine_distance(self.latitude, self.longitude, lat, lon)

from django.db import models
from django.conf import settings
from lost_items.models import CATEGORY_CHOICES, COLOUR_CHOICES

FOUND_STATUS_CHOICES = (
    ('available', 'Available'),
    ('claim_pending', 'Claim Pending'),
    ('claimed', 'Claimed'),
    ('handed_over', 'Handed Over'),
    ('closed', 'Closed'),
)


class FoundItem(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='found_items'
    )
    title = models.CharField(max_length=200, db_index=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, db_index=True)
    description = models.TextField()
    colour = models.CharField(max_length=50, choices=COLOUR_CHOICES, db_index=True)
    date_found = models.DateField(db_index=True)
    location_area = models.CharField(max_length=255)
    city = models.CharField(max_length=100, db_index=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    status = models.CharField(max_length=20, choices=FOUND_STATUS_CHOICES, default='available', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'found_items'
        verbose_name = 'Found Item'
        verbose_name_plural = 'Found Items'
        ordering = ['-created_at']

    def __str__(self):
        return f"[FOUND] {self.title} ({self.category}, {self.city})"

    @property
    def primary_image(self):
        img = self.images.filter(is_primary=True).first() or self.images.first()
        return img.image.url if img and img.image else None

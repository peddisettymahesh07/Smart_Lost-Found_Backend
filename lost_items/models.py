from django.db import models
from django.conf import settings

CATEGORY_CHOICES = (
    ('Electronics', 'Electronics'),
    ('Documents', 'Documents'),
    ('Accessories', 'Accessories'),
    ('Bags', 'Bags'),
    ('Jewellery', 'Jewellery'),
    ('Clothing', 'Clothing'),
    ('Books', 'Books'),
    ('Keys', 'Keys'),
    ('Wallets & Purses', 'Wallets & Purses'),
    ('Other', 'Other'),
)

COLOUR_CHOICES = (
    ('Black', 'Black'),
    ('Blue', 'Blue'),
    ('Red', 'Red'),
    ('White', 'White'),
    ('Silver', 'Silver'),
    ('Gold', 'Gold'),
    ('Brown', 'Brown'),
    ('Green', 'Green'),
    ('Yellow', 'Yellow'),
    ('Grey', 'Grey'),
    ('Orange', 'Orange'),
    ('Purple', 'Purple'),
    ('Pink', 'Pink'),
    ('Multi-colour', 'Multi-colour'),
    ('Other', 'Other'),
)

STATUS_CHOICES = (
    ('open', 'Open'),
    ('claimed', 'Claimed'),
    ('resolved', 'Resolved'),
    ('closed', 'Closed'),
)

CONTACT_PREFERENCES = (
    ('email', 'Email'),
    ('phone', 'Phone'),
    ('in_app', 'In-App Notifications'),
)


class LostItem(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='lost_items'
    )
    title = models.CharField(max_length=200, db_index=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, db_index=True)
    description = models.TextField()
    colour = models.CharField(max_length=50, choices=COLOUR_CHOICES, db_index=True)
    date_lost = models.DateField(db_index=True)
    location_area = models.CharField(max_length=255)
    city = models.CharField(max_length=100, db_index=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    contact_preference = models.CharField(max_length=20, choices=CONTACT_PREFERENCES, default='in_app')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'lost_items'
        verbose_name = 'Lost Item'
        verbose_name_plural = 'Lost Items'
        ordering = ['-created_at']

    def __str__(self):
        return f"[LOST] {self.title} ({self.category}, {self.city})"

    @property
    def primary_image(self):
        img = self.images.filter(is_primary=True).first() or self.images.first()
        return img.image.url if img and img.image else None

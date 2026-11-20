from django.db import models


class ItemImage(models.Model):
    lost_item = models.ForeignKey(
        'lost_items.LostItem',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='images'
    )
    found_item = models.ForeignKey(
        'found_items.FoundItem',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='images'
    )
    image = models.ImageField(upload_to='items/%Y/%m/%d/')
    embedding = models.JSONField(null=True, blank=True, help_text="512-dimensional image embedding vector")
    is_primary = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'item_images'
        verbose_name = 'Item Image'
        verbose_name_plural = 'Item Images'
        ordering = ['-is_primary', 'created_at']

    def __str__(self):
        target = f"LostItem #{self.lost_item_id}" if self.lost_item_id else f"FoundItem #{self.found_item_id}"
        return f"Image #{self.id} for {target}"


class MatchRecord(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending Review'),
        ('reviewed', 'Reviewed'),
        ('confirmed_match', 'Confirmed Match'),
        ('rejected', 'Rejected Match'),
        ('claim_submitted', 'Claim Submitted'),
    )

    CONFIDENCE_CHOICES = (
        ('High', 'High Match (>= 75%)'),
        ('Medium', 'Medium Match (50% - 74%)'),
        ('Low', 'Low Match (< 50%)'),
    )

    lost_item = models.ForeignKey(
        'lost_items.LostItem',
        on_delete=models.CASCADE,
        related_name='matches'
    )
    found_item = models.ForeignKey(
        'found_items.FoundItem',
        on_delete=models.CASCADE,
        related_name='matches'
    )
    image_similarity = models.FloatField(default=0.0)
    category_similarity = models.FloatField(default=0.0)
    colour_similarity = models.FloatField(default=0.0)
    description_similarity = models.FloatField(default=0.0)
    location_similarity = models.FloatField(default=0.0)
    date_similarity = models.FloatField(default=0.0)
    combined_score = models.FloatField(default=0.0, db_index=True)
    confidence_level = models.CharField(max_length=20, choices=CONFIDENCE_CHOICES, default='Low')
    distance_km = models.FloatField(null=True, blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    explanation = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'match_records'
        verbose_name = 'Match Record'
        verbose_name_plural = 'Match Records'
        ordering = ['-combined_score', '-created_at']
        constraints = [
            models.UniqueConstraint(fields=['lost_item', 'found_item'], name='unique_lost_found_match')
        ]

    def __str__(self):
        return f"Match: Lost #{self.lost_item_id} <-> Found #{self.found_item_id} ({self.combined_score:.1f}% - {self.confidence_level})"

from django.db import models
from django.conf import settings


class ClaimRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending Review'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    found_item = models.ForeignKey(
        'found_items.FoundItem',
        on_delete=models.CASCADE,
        related_name='claims'
    )
    lost_item = models.ForeignKey(
        'lost_items.LostItem',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='claims'
    )
    claimant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='claims_submitted'
    )
    proof_description = models.TextField(
        help_text="Private identifying information, distinctive marks, wallpapers, internal contents"
    )
    secret_identifiers = models.TextField(
        blank=True,
        help_text="Confidential serial numbers, invoice details, passcode hints, or answers to verification questions"
    )
    proof_document = models.ImageField(
        upload_to='claims/%Y/%m/',
        null=True,
        blank=True,
        help_text="Optional receipt, warranty card, or photograph proving ownership"
    )
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    finder_response = models.TextField(blank=True, help_text="Finder comments or verification notes")
    admin_notes = models.TextField(blank=True, help_text="Internal notes written by reviewing administrator")
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='claims_reviewed'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'claim_requests'
        verbose_name = 'Claim Request'
        verbose_name_plural = 'Claim Requests'
        ordering = ['-created_at']

    def __str__(self):
        return f"Claim #{self.id} for Found #{self.found_item_id} by {self.claimant.email} [{self.status}]"

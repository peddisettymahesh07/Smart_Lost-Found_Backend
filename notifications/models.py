from django.db import models
from django.conf import settings


class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('match_found', 'Potential AI Match Found'),
        ('new_match', 'New Possible Match Available'),
        ('claim_submitted', 'Ownership Claim Submitted'),
        ('claim_approved', 'Ownership Claim Approved'),
        ('claim_rejected', 'Ownership Claim Rejected'),
        ('status_update', 'Report Status Updated'),
        ('admin_alert', 'Administrative Notice'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES, default='match_found', db_index=True)
    related_item_type = models.CharField(max_length=30, blank=True, null=True)  # 'lost', 'found', 'match', 'claim'
    related_item_id = models.PositiveIntegerField(null=True, blank=True)
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'notifications'
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']

    def __str__(self):
        status_flag = "READ" if self.is_read else "UNREAD"
        return f"[{status_flag}] {self.user.email}: {self.title}"

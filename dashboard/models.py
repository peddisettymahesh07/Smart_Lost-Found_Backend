from django.db import models
from django.conf import settings


class AdminAction(models.Model):
    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='admin_actions'
    )
    action = models.CharField(max_length=100, db_index=True)
    target_type = models.CharField(max_length=50, db_index=True)
    target_id = models.PositiveIntegerField(db_index=True)
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'admin_actions'
        verbose_name = 'Admin Action'
        verbose_name_plural = 'Admin Actions'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.admin.email} -> {self.action} on {self.target_type} #{self.target_id} @ {self.created_at}"

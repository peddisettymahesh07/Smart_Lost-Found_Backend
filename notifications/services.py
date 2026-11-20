import logging
from django.core.mail import send_mail
from django.conf import settings
from .models import Notification

logger = logging.getLogger(__name__)


def create_notification(user, title, message, notification_type='match_found', related_item_type=None, related_item_id=None, send_email_alert=True):
    """
    Creates an in-app notification and sends an email alert to the user.
    """
    notification = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        related_item_type=related_item_type,
        related_item_id=related_item_id,
        is_read=False
    )

    if send_email_alert and user.email:
        subject = f"[Smart Lost & Found] {title}"
        email_body = f"""Hello {user.full_name or user.email},

{message}

Visit the Smart Lost & Found Platform to view details:
http://localhost:5173/

Best regards,
Smart Lost & Found Team
"""
        try:
            send_mail(
                subject=subject,
                message=email_body,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@smartlostfound.local'),
                recipient_list=[user.email],
                fail_silently=True,
            )
        except Exception as e:
            logger.warning(f"Failed to dispatch email to {user.email}: {e}")

    return notification

from .models import SystemLog
from django.contrib.auth.models import User
from django.utils.timezone import now

def log_system_action(user, action, description, ip_address=None):
    """
    Helper function to log system actions.
    """
    SystemLog.objects.create(
        user=user,
        action=action,
        description=description,
        ip_address=ip_address
    )
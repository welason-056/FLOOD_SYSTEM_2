from django.db import models
from django.contrib.auth.models import User


class Community(models.Model):
    name = models.CharField(max_length=100, unique=True)
    latitude = models.FloatField()
    longitude = models.FloatField()

    def __str__(self):
        return self.name


class Profile(models.Model):
    """
    One-to-one extension of the User model to store the community
    a user belongs to.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    community = models.ForeignKey(
        Community,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.user.username} - {self.community.name if self.community else 'No community'}"


class DailyFloodRisk(models.Model):
    RISK_CHOICES = [
        ('LOW', 'Low'),
        ('MODERATE', 'Moderate'),
        ('HIGH', 'High'),
    ]

    community = models.ForeignKey(Community, on_delete=models.CASCADE)
    date = models.DateField()
    rainfall_mm = models.FloatField()
    temperature_c = models.FloatField()
    humidity_percent = models.FloatField()
    soil_moisture = models.FloatField()
    flood_risk = models.BooleanField()
    confidence = models.FloatField()
    risk_level = models.CharField(
        max_length=10,
        choices=RISK_CHOICES,
        default='LOW'
    )

    class Meta:
        unique_together = ('community', 'date')

    def __str__(self):
        status = "FLOOD" if self.flood_risk else "SAFE"
        return f"{self.community.name} - {self.date} - {status}"
    from django.contrib.auth.models import User

class SystemLog(models.Model):
    ACTION_CHOICES = [
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('PREDICTION', 'Prediction Generated'),
        ('ALERT_SENT', 'Alert Sent'),
        ('ALERT_RESOLVED', 'Alert Resolved'),
        ('PREDICTION_DELETED', 'Prediction Deleted'),
        ('REPORT_GENERATED', 'Report Generated'),
        ('BACKUP_CREATED', 'Backup Created'),
        ('SYSTEM_ERROR', 'System Error'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.created_at} - {self.user} - {self.get_action_display()}"
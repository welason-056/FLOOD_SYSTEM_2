from django.contrib import admin
from .models import Community, DailyFloodRisk, Profile

@admin.register(Community)
class CommunityAdmin(admin.ModelAdmin):
    list_display = ('name', 'latitude', 'longitude')
    search_fields = ('name',)

@admin.register(DailyFloodRisk)
class DailyFloodRiskAdmin(admin.ModelAdmin):
    list_display = ('community', 'date', 'risk_level', 'flood_risk', 'confidence')
    list_filter = ('risk_level', 'flood_risk', 'community')
    date_hierarchy = 'date'

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'community')
    search_fields = ('user__username', 'community__name')
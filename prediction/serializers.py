from rest_framework import serializers
from .models import Community, DailyFloodRisk

class CommunitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Community
        fields = ['id', 'name', 'latitude', 'longitude']

class DailyFloodRiskSerializer(serializers.ModelSerializer):
    community_name = serializers.CharField(source='community.name', read_only=True)
    
    class Meta:
        model = DailyFloodRisk
        fields = ['id', 'community', 'community_name', 'date', 'rainfall_mm', 
                  'temperature_c', 'humidity_percent', 'soil_moisture', 
                  'flood_risk', 'confidence']
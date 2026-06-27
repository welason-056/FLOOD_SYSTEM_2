from django.core.management.base import BaseCommand
from prediction.models import RegionVulnerability, EvacuationCenter
import random


class Command(BaseCommand):
    help = 'Setup vulnerability data and evacuation centers'
    
    def handle(self, *args, **options):
        self.stdout.write("Setting up region vulnerability data...")
        
        vulnerability_data = {
            "Dar-es-salaam": {"elevation": 5, "distance_to_river": 1, "coastal": True, "drainage": 30, "protected": False, "population": 5000},
            "Morogoro": {"elevation": 50, "distance_to_river": 3, "coastal": False, "drainage": 50, "protected": False, "population": 500},
            "Mwanza": {"elevation": 40, "distance_to_river": 2, "coastal": False, "drainage": 45, "protected": False, "population": 800},
            "Tanga": {"elevation": 8, "distance_to_river": 1.5, "coastal": True, "drainage": 35, "protected": False, "population": 600},
            "Arusha": {"elevation": 120, "distance_to_river": 5, "coastal": False, "drainage": 60, "protected": False, "population": 400},
            "Kilimanjaro": {"elevation": 90, "distance_to_river": 4, "coastal": False, "drainage": 55, "protected": False, "population": 300},
            "Mbeya": {"elevation": 80, "distance_to_river": 3.5, "coastal": False, "drainage": 50, "protected": False, "population": 350},
            "Iringa": {"elevation": 100, "distance_to_river": 4, "coastal": False, "drainage": 55, "protected": False, "population": 250},
            "Kigoma": {"elevation": 60, "distance_to_river": 2, "coastal": False, "drainage": 40, "protected": False, "population": 300},
            "Lindi": {"elevation": 10, "distance_to_river": 1, "coastal": True, "drainage": 30, "protected": False, "population": 400},
            "Mtwara": {"elevation": 12, "distance_to_river": 1.2, "coastal": True, "drainage": 32, "protected": False, "population": 350},
            "Pwani": {"elevation": 15, "distance_to_river": 1.5, "coastal": True, "drainage": 35, "protected": False, "population": 450},
            "Ruvuma": {"elevation": 70, "distance_to_river": 3, "coastal": False, "drainage": 50, "protected": False, "population": 200},
            "Shinyanga": {"elevation": 55, "distance_to_river": 2.5, "coastal": False, "drainage": 45, "protected": False, "population": 250},
            "Singida": {"elevation": 65, "distance_to_river": 3, "coastal": False, "drainage": 50, "protected": False, "population": 180},
            "Tabora": {"elevation": 60, "distance_to_river": 2.8, "coastal": False, "drainage": 48, "protected": False, "population": 220},
            "Dodoma": {"elevation": 70, "distance_to_river": 3.2, "coastal": False, "drainage": 52, "protected": False, "population": 280},
        }
        
        for region, data in vulnerability_data.items():
            obj, created = RegionVulnerability.objects.update_or_create(
                region=region,
                defaults={
                    'elevation_meters': data['elevation'],
                    'distance_to_river_km': data['distance_to_river'],
                    'is_coastal': data['coastal'],
                    'drainage_quality': data['drainage'],
                    'flood_protection_present': data['protected'],
                    'population_density': data['population']
                }
            )
            if created:
                self.stdout.write(f"  ✅ Created: {region}")
            else:
                self.stdout.write(f"  🔄 Updated: {region}")
        
        self.stdout.write("\nSetting up evacuation centers...")
        
        centers_data = [
            {"name": "Benjamin Mkapa Stadium", "region": "Dar-es-salaam", "lat": -6.845, "lon": 39.267, "capacity": 5000, "phone": "+255 22 2850234", "address": "Kurasini, Dar es Salaam"},
            {"name": "Diamond Jubilee Hall", "region": "Dar-es-salaam", "lat": -6.816, "lon": 39.280, "capacity": 2000, "phone": "+255 22 2134567", "address": "Upanga, Dar es Salaam"},
            {"name": "Mwalimu Nyerere Grounds", "region": "Morogoro", "lat": -6.824, "lon": 37.661, "capacity": 3000, "phone": "+255 23 2601234", "address": "Morogoro Town"},
            {"name": "CCM Kirumba Stadium", "region": "Mwanza", "lat": -2.516, "lon": 32.917, "capacity": 3500, "phone": "+255 28 2545678", "address": "Mwanza City"},
            {"name": "Mkwakwani Stadium", "region": "Tanga", "lat": -5.069, "lon": 39.099, "capacity": 2500, "phone": "+255 27 2648901", "address": "Tanga City"},
            {"name": "Sheikh Amri Abeid Stadium", "region": "Arusha", "lat": -3.367, "lon": 36.683, "capacity": 2000, "phone": "+255 27 2501234", "address": "Arusha City"},
            {"name": "Uhuru Stadium", "region": "Dar-es-salaam", "lat": -6.830, "lon": 39.290, "capacity": 4000, "phone": "+255 22 2123456", "address": "Ilala, Dar es Salaam"},
            {"name": "Tungi Stadium", "region": "Pwani", "lat": -6.767, "lon": 38.917, "capacity": 1500, "phone": "+255 23 2403456", "address": "Kibaha, Pwani"},
        ]
        
        for center in centers_data:
            obj, created = EvacuationCenter.objects.update_or_create(
                name=center["name"],
                defaults={
                    'region': center["region"],
                    'latitude': center["lat"],
                    'longitude': center["lon"],
                    'capacity': center["capacity"],
                    'phone': center["phone"],
                    'address': center["address"]
                }
            )
            if created:
                self.stdout.write(f"  ✅ Created: {center['name']}")
        
        self.stdout.write(self.style.SUCCESS("\n✅ Setup complete!"))
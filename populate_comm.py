import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flood_system.settings')
django.setup()

from prediction.models import Community

communities = [
    ('Jangwani', -6.800, 39.269),
    ('Kigogo', -6.792, 39.255),
    ('Tandale', -6.775, 39.268),
    ('Hananasif', -6.780, 39.278),
    ('Vingunguti', -6.840, 39.258),
    ('Buguruni', -6.830, 39.250),
    ('Mbagala', -6.910, 39.310),
    ('Keko', -6.860, 39.270),
    ('Manzese', -6.800, 39.250),
    ('Sinza', -6.770, 39.240),
]

for name, lat, lon in communities:
    obj, created = Community.objects.get_or_create(name=name, defaults={'latitude': lat, 'longitude': lon})
    print(f"{'Created' if created else 'Exists'}: {name}")

print("✅ Communities added.")
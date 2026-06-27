from django.core.management.base import BaseCommand
from prediction.ml_model import ai_model


class Command(BaseCommand):
    help = 'Train AI model using FloodClimateData from database'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--region',
            type=str,
            help='Train for specific region only'
        )
    
    def handle(self, *args, **options):
        region = options.get('region')
        
        self.stdout.write("=" * 50)
        self.stdout.write("🤖 AI Model Training from Database")
        self.stdout.write("=" * 50)
        
        if region:
            self.stdout.write(f"📊 Training for region: {region}")
        else:
            self.stdout.write("📊 Training for ALL regions")
        
        self.stdout.write("")
        self.stdout.write("🔄 Fetching historical data from FloodClimateData...")
        
        success = ai_model.train_from_database(region)
        
        if success:
            ai_model.save_model('flood_ai_model.pkl')
            self.stdout.write("")
            self.stdout.write(self.style.SUCCESS("✅ Training Complete!"))
            self.stdout.write(f"   📈 Records used: {ai_model.training_records}")
            self.stdout.write(f"   🌍 Regions covered: {len(ai_model.trained_regions)}")
            self.stdout.write(f"   💾 Model saved to: flood_ai_model.pkl")
        else:
            self.stdout.write("")
            self.stdout.write(self.style.ERROR("❌ Training Failed!"))
            self.stdout.write("   Need at least 30 historical records per region")
        
        self.stdout.write("=" * 50)
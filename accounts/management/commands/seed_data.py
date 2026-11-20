import os
from io import BytesIO
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from PIL import Image, ImageDraw
from accounts.models import User
from lost_items.models import LostItem
from found_items.models import FoundItem
from matching.models import ItemImage
from matching.ai_engine import extract_image_embedding
from matching.services import run_matching_for_lost_item
from locations.models import Location
from claims.models import ClaimRequest


def create_mock_item_image(color_rgb, shape_type='rect', label="Item"):
    """Creates a real PNG image in memory for testing image feature extraction."""
    img = Image.new('RGB', (300, 300), color=(240, 240, 245))
    draw = ImageDraw.Draw(img)

    if shape_type == 'rect':
        draw.rectangle([40, 50, 260, 250], fill=color_rgb, outline=(30, 30, 30), width=3)
    elif shape_type == 'circle':
        draw.ellipse([50, 50, 250, 250], fill=color_rgb, outline=(30, 30, 30), width=3)
    elif shape_type == 'wallet':
        draw.rounded_rectangle([40, 80, 260, 220], radius=15, fill=color_rgb, outline=(20, 20, 20), width=4)
        draw.line([40, 150, 260, 150], fill=(220, 220, 220), width=2)
    elif shape_type == 'laptop':
        draw.rectangle([40, 60, 260, 200], fill=(40, 40, 45), outline=(100, 100, 100), width=2)
        draw.rectangle([60, 80, 240, 180], fill=color_rgb)
        draw.polygon([(20, 230), (280, 230), (260, 200), (40, 200)], fill=(70, 70, 75))

    buf = BytesIO()
    img.save(buf, format='PNG')
    return ContentFile(buf.getvalue(), name=f"{label.lower().replace(' ', '_')}.png")


class Command(BaseCommand):
    help = 'Seeds database with realistic demo users, lost/found items, AI embeddings, locations, and claims.'

    def handle(self, *args, **options):
        self.stdout.write("Starting database seeding...")

        # 1. Admin User
        admin_user, created = User.objects.get_or_create(
            email='admin@smartlostfound.com',
            defaults={
                'full_name': 'System Administrator',
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True,
                'phone_number': '+1-800-555-0100',
            }
        )
        if created:
            admin_user.set_password('Admin@12345')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS(f"Created Admin: {admin_user.email}"))

        # 2. General User (Owner)
        user1, created = User.objects.get_or_create(
            email='john.doe@example.com',
            defaults={
                'full_name': 'John Doe',
                'role': 'user',
                'phone_number': '+1-555-0199',
            }
        )
        if created:
            user1.set_password('User@12345')
            user1.save()
            self.stdout.write(self.style.SUCCESS(f"Created User: {user1.email}"))

        # 3. Item Finder
        finder1, created = User.objects.get_or_create(
            email='sarah.finder@example.com',
            defaults={
                'full_name': 'Sarah Jenkins',
                'role': 'finder',
                'phone_number': '+1-555-0144',
            }
        )
        if created:
            finder1.set_password('Finder@12345')
            finder1.save()
            self.stdout.write(self.style.SUCCESS(f"Created Finder: {finder1.email}"))

        # 4. Create Lost Items
        today = date.today()

        lost1, _ = LostItem.objects.get_or_create(
            user=user1,
            title='Dell XPS 15 Laptop in Black Sleeve',
            defaults={
                'category': 'Electronics',
                'description': 'Silver Dell XPS 15 (9520) with Intel i7 and carbon fiber palm rest. Was inside a padded black neoprene zip sleeve. Lost in the university main library 2nd floor reading hall.',
                'colour': 'Silver',
                'date_lost': today - timedelta(days=2),
                'location_area': 'Central Campus Library, Floor 2',
                'city': 'San Francisco',
                'latitude': 37.774929,
                'longitude': -122.419416,
                'contact_preference': 'email',
                'status': 'open'
            }
        )
        if not lost1.images.exists():
            img_file = create_mock_item_image((70, 130, 180), 'laptop', 'dell_laptop')
            embedding = extract_image_embedding(img_file)
            img_file.seek(0)
            ItemImage.objects.create(lost_item=lost1, image=img_file, embedding=embedding, is_primary=True)
            Location.objects.update_or_create(item_type='lost', item_id=lost1.id, defaults={
                'latitude': lost1.latitude, 'longitude': lost1.longitude, 'area': lost1.location_area, 'city': lost1.city
            })

        lost2, _ = LostItem.objects.get_or_create(
            user=user1,
            title='Navy Blue Tommy Hilfiger Leather Wallet',
            defaults={
                'category': 'Wallets & Purses',
                'description': 'Dark navy blue bifold leather wallet with small red and white logo emblem. Contains driver license and transit passes.',
                'colour': 'Blue',
                'date_lost': today - timedelta(days=4),
                'location_area': 'Metro Station Platform 3',
                'city': 'San Francisco',
                'latitude': 37.783333,
                'longitude': -122.416667,
                'contact_preference': 'in_app',
                'status': 'open'
            }
        )
        if not lost2.images.exists():
            img_file = create_mock_item_image((25, 45, 110), 'wallet', 'blue_wallet')
            embedding = extract_image_embedding(img_file)
            img_file.seek(0)
            ItemImage.objects.create(lost_item=lost2, image=img_file, embedding=embedding, is_primary=True)
            Location.objects.update_or_create(item_type='lost', item_id=lost2.id, defaults={
                'latitude': lost2.latitude, 'longitude': lost2.longitude, 'area': lost2.location_area, 'city': lost2.city
            })

        # 5. Create Found Items
        found1, _ = FoundItem.objects.get_or_create(
            user=finder1,
            title='Dell Laptop in Black Sleeve',
            defaults={
                'category': 'Electronics',
                'description': 'Found a silver Dell laptop in a black protective sleeve left on table near window in library study area.',
                'colour': 'Silver',
                'date_found': today - timedelta(days=2),
                'location_area': 'Campus Library 2nd Floor Window Table',
                'city': 'San Francisco',
                'latitude': 37.775100,
                'longitude': -122.419200,
                'status': 'available'
            }
        )
        if not found1.images.exists():
            img_file = create_mock_item_image((75, 135, 185), 'laptop', 'found_dell')
            embedding = extract_image_embedding(img_file)
            img_file.seek(0)
            ItemImage.objects.create(found_item=found1, image=img_file, embedding=embedding, is_primary=True)
            Location.objects.update_or_create(item_type='found', item_id=found1.id, defaults={
                'latitude': found1.latitude, 'longitude': found1.longitude, 'area': found1.location_area, 'city': found1.city
            })

        found2, _ = FoundItem.objects.get_or_create(
            user=finder1,
            title='Blue Leather Bifold Wallet',
            defaults={
                'category': 'Wallets & Purses',
                'description': 'Found dark blue men leather wallet on bench near ticket counter.',
                'colour': 'Blue',
                'date_found': today - timedelta(days=3),
                'location_area': 'Downtown Metro Concourse',
                'city': 'San Francisco',
                'latitude': 37.784000,
                'longitude': -122.415000,
                'status': 'available'
            }
        )
        if not found2.images.exists():
            img_file = create_mock_item_image((28, 48, 115), 'wallet', 'found_wallet')
            embedding = extract_image_embedding(img_file)
            img_file.seek(0)
            ItemImage.objects.create(found_item=found2, image=img_file, embedding=embedding, is_primary=True)
            Location.objects.update_or_create(item_type='found', item_id=found2.id, defaults={
                'latitude': found2.latitude, 'longitude': found2.longitude, 'area': found2.location_area, 'city': found2.city
            })

        # 6. Trigger AI Matching
        self.stdout.write("Running AI matching engine on demo records...")
        run_matching_for_lost_item(lost1)
        run_matching_for_lost_item(lost2)

        # 7. Create a Sample Claim Request
        claim, _ = ClaimRequest.objects.get_or_create(
            found_item=found1,
            claimant=user1,
            defaults={
                'lost_item': lost1,
                'proof_description': 'The laptop has a small scratch on bottom left corner near the ventilation grill. Desktop wallpaper is Yosemite Valley at sunset.',
                'secret_identifiers': 'Service Tag Serial: 87DFX92. Windows username: jdoe. Lock PIN starts with 94.',
                'status': 'pending',
                'finder_response': 'Waiting for claimant to confirm the exact serial number and lock wallpaper.'
            }
        )

        self.stdout.write(self.style.SUCCESS("Database seeded successfully with demo users, items, real embeddings, matches, locations, and claims!"))

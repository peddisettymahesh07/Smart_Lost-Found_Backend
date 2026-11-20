from django.test import TestCase
from datetime import date, timedelta
from accounts.models import User
from lost_items.models import LostItem
from found_items.models import FoundItem
from matching.models import ItemImage, MatchRecord
from matching.ai_engine import (
    extract_vision_embedding_fallback,
    calculate_cosine_similarity,
    calculate_combined_match_score,
)
from matching.services import run_matching_for_lost_item
from accounts.management.commands.seed_data import create_mock_item_image


class AIMatchingEngineTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='Password@123',
            full_name='Test User',
            role='user'
        )
        self.finder = User.objects.create_user(
            email='testfinder@example.com',
            password='Password@123',
            full_name='Test Finder',
            role='finder'
        )

    def test_vision_embedding_extraction_and_cosine_similarity(self):
        img_red = create_mock_item_image((255, 0, 0), 'rect', 'red')
        img_red_copy = create_mock_item_image((250, 5, 5), 'rect', 'red_copy')
        img_blue = create_mock_item_image((0, 0, 255), 'circle', 'blue')

        emb_red1 = extract_vision_embedding_fallback(img_red)
        emb_red2 = extract_vision_embedding_fallback(img_red_copy)
        emb_blue = extract_vision_embedding_fallback(img_blue)

        # Check embedding properties
        self.assertEqual(len(emb_red1), 512)
        self.assertEqual(len(emb_blue), 512)

        # Identical/similar images must have high cosine similarity
        sim_same = calculate_cosine_similarity(emb_red1, emb_red2)
        sim_diff = calculate_cosine_similarity(emb_red1, emb_blue)

        self.assertGreater(sim_same, 80.0)
        self.assertGreater(sim_same, sim_diff)

    def test_multi_factor_matching_and_notification(self):
        today = date.today()

        lost = LostItem.objects.create(
            user=self.user,
            title='Black Apple iPhone 14 Pro',
            category='Electronics',
            description='Lost black iPhone 14 Pro with dark silicone case and broken screen protector.',
            colour='Black',
            date_lost=today,
            location_area='Terminal 2 Baggage Claim',
            city='Boston',
            latitude=42.3656,
            longitude=-71.0096,
        )
        img_file1 = create_mock_item_image((20, 20, 20), 'rect', 'iphone_lost')
        ItemImage.objects.create(lost_item=lost, image=img_file1, embedding=extract_vision_embedding_fallback(img_file1))

        found = FoundItem.objects.create(
            user=self.finder,
            title='Apple iPhone with black case',
            category='Electronics',
            description='Found iPhone with black case near airport baggage carousel.',
            colour='Black',
            date_found=today,
            location_area='Terminal 2 Arrival Gate',
            city='Boston',
            latitude=42.3658,
            longitude=-71.0094,
        )
        img_file2 = create_mock_item_image((22, 22, 22), 'rect', 'iphone_found')
        ItemImage.objects.create(found_item=found, image=img_file2, embedding=extract_vision_embedding_fallback(img_file2))

        # Run matching
        matches = run_matching_for_lost_item(lost)
        self.assertGreaterEqual(len(matches), 1)

        match = matches[0]
        self.assertEqual(match.found_item, found)
        self.assertGreaterEqual(match.combined_score, 75.0)
        self.assertEqual(match.confidence_level, 'High')
        self.assertIn("AI Combined Match", match.explanation)

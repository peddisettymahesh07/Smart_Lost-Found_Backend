from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from datetime import date
from accounts.models import User
from lost_items.models import LostItem
from found_items.models import FoundItem
from claims.models import ClaimRequest
from notifications.models import Notification
from matching.models import MatchRecord
from accounts.management.commands.seed_data import create_mock_item_image


class EndToEndPlatformWorkflowTestCase(APITestCase):
    def test_complete_platform_lifecycle(self):
        # 1. User Registration
        register_url = reverse('auth_register')
        reg_payload = {
            'full_name': 'David Miller',
            'email': 'david.miller@example.com',
            'password': 'DavidPassword@123',
            'confirm_password': 'DavidPassword@123',
            'role': 'user',
        }
        reg_resp = self.client.post(register_url, reg_payload)
        self.assertEqual(reg_resp.status_code, status.HTTP_201_CREATED)
        david_token = reg_resp.data['access']

        # 2. Finder Registration
        finder_payload = {
            'full_name': 'Emma Watson',
            'email': 'emma.finder@example.com',
            'password': 'EmmaPassword@123',
            'confirm_password': 'EmmaPassword@123',
            'role': 'finder',
        }
        finder_resp = self.client.post(register_url, finder_payload)
        self.assertEqual(finder_resp.status_code, status.HTTP_201_CREATED)
        emma_token = finder_resp.data['access']

        # 3. David reports a Lost Item with an actual image
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {david_token}')
        lost_img = create_mock_item_image((30, 60, 150), 'rect', 'blue_backpack')

        lost_data = {
            'title': 'Blue North Face Hiking Backpack',
            'category': 'Bags',
            'description': 'Navy blue North Face Terra 55L backpack with yellow cord accents. Contains hiking trail guides.',
            'colour': 'Blue',
            'date_lost': str(date.today()),
            'location_area': 'Pine Crest Trailhead',
            'city': 'Denver',
            'latitude': '39.7392',
            'longitude': '-104.9903',
            'contact_preference': 'email',
            'image': lost_img,
        }
        lost_resp = self.client.post(reverse('lost_item_list_create'), lost_data, format='multipart')
        self.assertEqual(lost_resp.status_code, status.HTTP_201_CREATED)
        lost_id = lost_resp.data['id']

        # 4. Emma reports a Found Item with an actual image in Denver
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {emma_token}')
        found_img = create_mock_item_image((32, 62, 148), 'rect', 'found_blue_backpack')

        found_data = {
            'title': 'North Face Blue Backpack',
            'category': 'Bags',
            'description': 'Found blue hiking backpack near trail rest bench.',
            'colour': 'Blue',
            'date_found': str(date.today()),
            'location_area': 'Pine Crest Trailhead Rest Area',
            'city': 'Denver',
            'latitude': '39.7395',
            'longitude': '-104.9900',
            'image': found_img,
        }
        found_resp = self.client.post(reverse('found_item_list_create'), found_data, format='multipart')
        self.assertEqual(found_resp.status_code, status.HTTP_201_CREATED)
        found_id = found_resp.data['id']

        # 5. Verify AI similarity record was generated
        matches = MatchRecord.objects.filter(lost_item_id=lost_id, found_item_id=found_id)
        self.assertTrue(matches.exists(), "AI MatchRecord must be automatically created")
        match = matches.first()
        self.assertGreaterEqual(match.combined_score, 70.0)
        self.assertIn(match.confidence_level, ['High', 'Medium'])

        # 6. Verify Notifications dispatched
        david_user = User.objects.get(email='david.miller@example.com')
        notifs = Notification.objects.filter(user=david_user)
        self.assertTrue(notifs.exists(), "David must receive notification of AI match")

        # 7. David files an ownership claim
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {david_token}')
        claim_data = {
            'found_item': found_id,
            'lost_item': lost_id,
            'proof_description': 'Has a green carabiner on left shoulder strap and Colorado park sticker on bottom pouch.',
            'secret_identifiers': 'Name tag inside top flap: D. Miller #5541',
        }
        claim_resp = self.client.post(reverse('claim_list_create'), claim_data)
        self.assertEqual(claim_resp.status_code, status.HTTP_201_CREATED)
        claim_id = claim_resp.data['id']

        # 8. Emma reviews and approves claim
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {emma_token}')
        approve_resp = self.client.patch(
            reverse('claim_status_update', args=[claim_id]),
            {'status': 'approved', 'finder_response': 'Carabiner and name tag verified. Pick up at trail center.'}
        )
        self.assertEqual(approve_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(approve_resp.data['claim']['status'], 'approved')

        # Check item statuses
        found_obj = FoundItem.objects.get(pk=found_id)
        lost_obj = LostItem.objects.get(pk=lost_id)
        self.assertEqual(found_obj.status, 'claimed')
        self.assertEqual(lost_obj.status, 'claimed')

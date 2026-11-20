from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from datetime import date
from accounts.models import User
from found_items.models import FoundItem
from claims.models import ClaimRequest


class OwnershipVerificationTestCase(APITestCase):
    def setUp(self):
        self.finder = User.objects.create_user(
            email='finder@example.com',
            password='Password@123',
            full_name='Finder Frank',
            role='finder'
        )
        self.claimant = User.objects.create_user(
            email='claimant@example.com',
            password='Password@123',
            full_name='Claimant Chloe',
            role='user'
        )
        self.other_user = User.objects.create_user(
            email='stranger@example.com',
            password='Password@123',
            full_name='Stranger Stan',
            role='user'
        )
        self.admin = User.objects.create_user(
            email='admin@example.com',
            password='Password@123',
            full_name='Admin Alex',
            role='admin',
            is_staff=True
        )

        self.found_item = FoundItem.objects.create(
            user=self.finder,
            title='Gold Wedding Ring',
            category='Jewellery',
            description='Found a gold band ring engraved inside.',
            colour='Gold',
            date_found=date.today(),
            location_area='Park Bench',
            city='Seattle'
        )

    def test_submit_claim_and_privacy_restriction(self):
        # 1. Claimant submits claim with private secret identifier
        self.client.force_authenticate(user=self.claimant)
        claim_data = {
            'found_item': self.found_item.id,
            'proof_description': '18k yellow gold band with inscription "Forever & Always J&C 2021"',
            'secret_identifiers': 'Serial hallmark #925-AU750 inside the band',
        }
        submit_resp = self.client.post(reverse('claim_list_create'), claim_data)
        self.assertEqual(submit_resp.status_code, status.HTTP_201_CREATED)
        claim_id = submit_resp.data['id']

        # 2. Claimant can see their own proof description
        detail_resp = self.client.get(reverse('claim_detail', args=[claim_id]))
        self.assertEqual(detail_resp.status_code, status.HTTP_200_OK)
        self.assertIn('Forever & Always', detail_resp.data['proof_description'])

        # 3. Third-party stranger CANNOT see the claim
        self.client.force_authenticate(user=self.other_user)
        stranger_resp = self.client.get(reverse('claim_detail', args=[claim_id]))
        self.assertEqual(stranger_resp.status_code, status.HTTP_404_NOT_FOUND)

        # 4. Finder can review and respond
        self.client.force_authenticate(user=self.finder)
        finder_resp = self.client.patch(
            reverse('claim_status_update', args=[claim_id]),
            {'status': 'approved', 'finder_response': 'Inscription matches! Ready to return.'}
        )
        self.assertEqual(finder_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(finder_resp.data['claim']['status'], 'approved')

        # Check item status updated
        self.found_item.refresh_from_db()
        self.assertEqual(self.found_item.status, 'claimed')

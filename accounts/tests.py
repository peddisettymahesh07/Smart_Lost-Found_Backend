from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import User


class AuthenticationAPITestCase(APITestCase):
    def setUp(self):
        self.register_url = reverse('auth_register')
        self.login_url = reverse('auth_login')
        self.profile_url = reverse('auth_profile')

    def test_user_registration_success(self):
        data = {
            'full_name': 'Alice Smith',
            'email': 'alice.smith@example.com',
            'password': 'SecurePassword@123',
            'confirm_password': 'SecurePassword@123',
            'role': 'user',
            'phone_number': '+1-555-0188',
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['email'], 'alice.smith@example.com')

    def test_registration_password_mismatch_fails(self):
        data = {
            'full_name': 'Bob Smith',
            'email': 'bob.smith@example.com',
            'password': 'Password@123',
            'confirm_password': 'MismatchPassword@999',
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('confirm_password', response.data)

    def test_user_login_and_profile_access(self):
        user = User.objects.create_user(
            email='carol@example.com',
            password='CarolPassword@123',
            full_name='Carol Danvers',
            role='finder'
        )
        login_data = {
            'email': 'carol@example.com',
            'password': 'CarolPassword@123'
        }
        login_resp = self.client.post(self.login_url, login_data)
        self.assertEqual(login_resp.status_code, status.HTTP_200_OK)
        access_token = login_resp.data['access']

        # Access protected profile
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        profile_resp = self.client.get(self.profile_url)
        self.assertEqual(profile_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(profile_resp.data['full_name'], 'Carol Danvers')

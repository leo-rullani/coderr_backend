import pytest
from rest_framework.test import APIClient
from django.urls import reverse
from auth_app.models import CustomUser
from users_app.models import UserProfile

@pytest.mark.django_db
class TestUserProfilesAPI:
    """
    Test suite for user profile API endpoints including listing,
    detail retrieval, update, authentication, and permission checks.
    """

    @pytest.fixture(autouse=True)
    def setup(self):
        """
        Setup method to create test users and authenticated API clients
        for business and customer roles.
        """
        # Create a business user with profile
        self.business_user = CustomUser.objects.create_user(
            username="business_test", password="testpass123", role="business"
        )
        UserProfile.objects.create(user=self.business_user, is_customer=False)

        # Create a customer user with profile
        self.customer_user = CustomUser.objects.create_user(
            username="customer_test", password="testpass123", role="customer"
        )
        UserProfile.objects.create(user=self.customer_user, is_customer=True)

        # Authenticate business user client
        self.client_business = APIClient()
        response = self.client_business.post(
            reverse("login"), {"username": "business_test", "password": "testpass123"}
        )
        self.token_business = response.data["token"]
        self.client_business.credentials(HTTP_AUTHORIZATION=f"Token {self.token_business}")

        # Authenticate customer user client
        self.client_customer = APIClient()
        response = self.client_customer.post(
            reverse("login"), {"username": "customer_test", "password": "testpass123"}
        )
        self.token_customer = response.data["token"]
        self.client_customer.credentials(HTTP_AUTHORIZATION=f"Token {self.token_customer}")

    def test_get_business_profiles(self):
        """
        Test retrieval of business user profiles list.
        Checks HTTP 200, presence of pagination results,
        and that the test business user is included.
        """
        url = reverse("business-profiles")
        response = self.client_business.get(url)
        assert response.status_code == 200
        assert "results" in response.data
        usernames = [profile["username"] for profile in response.data["results"]]
        assert "business_test" in usernames

    def test_get_customer_profiles(self):
        """
        Test retrieval of customer user profiles list.
        Checks HTTP 200, pagination structure,
        and inclusion of the test customer user.
        """
        url = reverse("customer-profiles")
        response = self.client_customer.get(url)
        assert response.status_code == 200
        assert "results" in response.data
        usernames = [profile["username"] for profile in response.data["results"]]
        assert "customer_test" in usernames

    def test_get_user_profile_detail(self):
        """
        Test retrieval of a specific user's profile detail.
        Checks HTTP 200 and correct username in the response.
        """
        url = reverse("user-profile-detail", kwargs={"pk": self.customer_user.id})
        response = self.client_customer.get(url)
        assert response.status_code == 200
        assert response.data["username"] == "customer_test"

    def test_patch_user_profile(self):
        """
        Test partial update (PATCH) of user profile fields.
        Checks HTTP 200 and verifies updated fields in the response.
        """
        url = reverse("user-profile-detail", kwargs={"pk": self.customer_user.id})
        data = {
            "first_name": "Test",
            "last_name": "User",
            "location": "Berlin",
            "tel": "12345678"
        }
        response = self.client_customer.patch(url, data, format="json")
        assert response.status_code == 200
        assert response.data["first_name"] == "Test"
        assert response.data["location"] == "Berlin"

    def test_unauthorized_access(self):
        """
        Test access without authentication to a protected endpoint.
        Expects HTTP 401 Unauthorized response.
        """
        url = reverse("business-profiles")
        client = APIClient()  # No authentication
        response = client.get(url)
        assert response.status_code == 401

    def test_forbidden_profile_update(self):
        """
        Test that a customer cannot update a business user's profile.
        Expects HTTP 403 Forbidden response.
        """
        url = reverse("user-profile-detail", kwargs={"pk": self.business_user.id})
        data = {"first_name": "Hacker"}
        response = self.client_customer.patch(url, data, format="json")
        assert response.status_code == 403

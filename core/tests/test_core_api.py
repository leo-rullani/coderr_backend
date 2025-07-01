import pytest
from rest_framework.test import APIClient
from django.urls import reverse

@pytest.mark.django_db
class TestBaseInfoAPI:
    def setup_method(self):
        self.client = APIClient()

    def test_base_info_success(self):
        url = reverse("base-info")
        response = self.client.get(url)
        assert response.status_code == 200
        data = response.data
        # Check fields are present and correct types
        assert "review_count" in data
        assert "average_rating" in data
        assert "business_profile_count" in data
        assert "offer_count" in data
        assert isinstance(data["review_count"], int)
        assert isinstance(data["average_rating"], float)
        assert isinstance(data["business_profile_count"], int)
        assert isinstance(data["offer_count"], int)
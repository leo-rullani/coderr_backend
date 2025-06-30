import pytest
from rest_framework.test import APIClient
from django.urls import reverse
from reviews_app.models import Review
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.mark.django_db
class TestReviewListAPI:
    def setup_method(self):
        self.client = APIClient()
        self.reviewer1 = User.objects.create_user(username='reviewer1', password='pw123')
        self.reviewer2 = User.objects.create_user(username='reviewer2', password='pw123')
        self.business1 = User.objects.create_user(username='biz1', password='pw123')
        self.business2 = User.objects.create_user(username='biz2', password='pw123')

        # Reviews anlegen
        Review.objects.create(
            business_user=self.business1,
            reviewer=self.reviewer1,
            rating=5,
            description="Review A"
        )
        Review.objects.create(
            business_user=self.business1,
            reviewer=self.reviewer2,
            rating=2,
            description="Review B"
        )
        Review.objects.create(
            business_user=self.business2,
            reviewer=self.reviewer1,
            rating=4,
            description="Review C"
        )

    def test_list_reviews_authenticated(self):
        self.client.force_authenticate(user=self.reviewer1)
        url = reverse('review-list')
        response = self.client.get(url)
        assert response.status_code == 200
        data = response.data if isinstance(response.data, list) else response.data['results']
        assert len(data) == 3

    def test_list_reviews_unauthenticated(self):
        url = reverse('review-list')
        response = self.client.get(url)
        assert response.status_code == 401

    def test_filter_by_business_user(self):
        self.client.force_authenticate(user=self.reviewer1)
        url = reverse('review-list') + f'?business_user={self.business1.id}'
        response = self.client.get(url)
        assert response.status_code == 200
        data = response.data if isinstance(response.data, list) else response.data['results']
        assert all(r['business_user'] == self.business1.id for r in data)
        assert len(data) == 2

    def test_filter_by_reviewer(self):
        self.client.force_authenticate(user=self.reviewer1)
        url = reverse('review-list') + f'?reviewer={self.reviewer2.id}'
        response = self.client.get(url)
        assert response.status_code == 200
        data = response.data if isinstance(response.data, list) else response.data['results']
        assert all(r['reviewer'] == self.reviewer2.id for r in data)
        assert len(data) == 1

    def test_ordering_by_rating(self):
        self.client.force_authenticate(user=self.reviewer1)
        url = reverse('review-list') + '?ordering=rating'
        response = self.client.get(url)
        assert response.status_code == 200
        data = response.data if isinstance(response.data, list) else response.data['results']
        ratings = [r['rating'] for r in data]
        assert ratings == sorted(ratings)
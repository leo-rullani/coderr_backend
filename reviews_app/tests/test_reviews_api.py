import pytest
from rest_framework.test import APIClient
from django.urls import reverse
from reviews_app.models import Review
from django.contrib.auth import get_user_model
from users_app.models import UserProfile

User = get_user_model()

@pytest.mark.django_db
class TestReviewListAPI:
    def setup_method(self):
        self.client = APIClient()
        self.reviewer1 = User.objects.create_user(username='reviewer1', password='pw123')
        UserProfile.objects.create(user=self.reviewer1, is_customer=True)
        self.reviewer2 = User.objects.create_user(username='reviewer2', password='pw123')
        UserProfile.objects.create(user=self.reviewer2, is_customer=True)
        self.business1 = User.objects.create_user(username='biz1', password='pw123')
        UserProfile.objects.create(user=self.business1, is_customer=False)
        self.business2 = User.objects.create_user(username='biz2', password='pw123')
        UserProfile.objects.create(user=self.business2, is_customer=False)
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

@pytest.mark.django_db
class TestReviewPOST:
    def setup_method(self):
        self.client = APIClient()
        self.customer = User.objects.create_user(username='kunde', password='pw123')
        UserProfile.objects.create(user=self.customer, is_customer=True)
        self.customer2 = User.objects.create_user(username='kunde2', password='pw123')
        UserProfile.objects.create(user=self.customer2, is_customer=True)
        self.not_customer = User.objects.create_user(username='notkunde', password='pw123')
        UserProfile.objects.create(user=self.not_customer, is_customer=False)
        self.business = User.objects.create_user(username='business', password='pw123')
        UserProfile.objects.create(user=self.business, is_customer=False)

    def test_post_review_success(self):
        self.client.force_authenticate(user=self.customer)
        url = reverse('review-list')
        data = {
            "business_user": self.business.id,
            "rating": 5,
            "description": "Hervorragende Erfahrung!"
        }
        response = self.client.post(url, data)
        assert response.status_code == 201
        body = response.data
        assert body["business_user"] == self.business.id
        assert body["reviewer"] == self.customer.id
        assert body["rating"] == 5
        assert body["description"] == "Hervorragende Erfahrung!"

    def test_post_review_twice_same_business(self):
        self.client.force_authenticate(user=self.customer2)
        url = reverse('review-list')
        data = {
            "business_user": self.business.id,
            "rating": 4,
            "description": "Gut!"
        }

        response1 = self.client.post(url, data)
        assert response1.status_code == 201
        response2 = self.client.post(url, data)
        assert response2.status_code in (400, 403)
        assert "already reviewed" in str(response2.data["non_field_errors"][0])


    def test_post_review_unauthenticated(self):
        url = reverse('review-list')
        data = {
            "business_user": self.business.id,
            "rating": 5,
            "description": "Ohne Login"
        }
        response = self.client.post(url, data)
        assert response.status_code == 401

    def test_post_review_not_a_customer(self):
        self.client.force_authenticate(user=self.not_customer)
        url = reverse('review-list')
        data = {
            "business_user": self.business.id,
            "rating": 4,
            "description": "Ich bin kein Kunde"
        }
        response = self.client.post(url, data)
        assert response.status_code == 403
        assert "Nur Kunden" in str(response.data) or "customer" in str(response.data)
    
    def test_patch_review_by_owner(self):
        # Kunde erstellt Bewertung
        review = Review.objects.create(
            business_user=self.business,
            reviewer=self.customer,
            rating=3,
            description="Guter Service"
        )
        self.client.force_authenticate(user=self.customer)
        url = reverse('review-detail', args=[review.id])
        data = {
            "rating": 5,
            "description": "Noch besser als erwartet!"
        }
        response = self.client.patch(url, data)
        assert response.status_code == 200
        assert response.data["rating"] == 5
        assert response.data["description"] == "Noch besser als erwartet!"

    def test_patch_review_forbidden_for_non_owner(self):
        # Kunde1 erstellt Bewertung, Kunde2 versucht PATCH
        review = Review.objects.create(
            business_user=self.business,
            reviewer=self.customer,
            rating=3,
            description="Initial"
        )
        self.client.force_authenticate(user=self.customer2)
        url = reverse('review-detail', args=[review.id])
        data = {
            "rating": 1,
            "description": "Darf ich nicht ändern"
        }
        response = self.client.patch(url, data)
        assert response.status_code == 403

    def test_patch_review_unauthenticated(self):
        review = Review.objects.create(
            business_user=self.business,
            reviewer=self.customer,
            rating=3,
            description="Initial"
        )
        url = reverse('review-detail', args=[review.id])
        data = {
            "rating": 4,
            "description": "Test"
        }
        response = self.client.patch(url, data)
        assert response.status_code == 401

    def test_patch_review_invalid_rating(self):
        review = Review.objects.create(
            business_user=self.business,
            reviewer=self.customer,
            rating=3,
            description="Initial"
        )
        self.client.force_authenticate(user=self.customer)
        url = reverse('review-detail', args=[review.id])
        data = {
            "rating": 99,
            "description": "Unrealistisch"
        }
        response = self.client.patch(url, data)
        assert response.status_code == 400
        assert "Rating must be between 1 and 5." in str(response.data)

    def test_delete_review_by_owner(self):
        review = Review.objects.create(
            business_user=self.business,
            reviewer=self.customer,
            rating=3,
            description="Initial"
        )
        self.client.force_authenticate(user=self.customer)
        url = reverse('review-detail', args=[review.id])
        response = self.client.delete(url)
        assert response.status_code == 204

    def test_delete_review_forbidden_for_non_owner(self):
        review = Review.objects.create(
            business_user=self.business,
            reviewer=self.customer,
            rating=3,
            description="Initial"
        )
        self.client.force_authenticate(user=self.customer2)
        url = reverse('review-detail', args=[review.id])
        response = self.client.delete(url)
        assert response.status_code == 403
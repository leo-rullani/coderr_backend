import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from offers_app.models import Offer, OfferDetail
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()

@pytest.fixture
def business_user(db):
    user = User.objects.create_user(username="business_test", password="pw12345", role="business")
    return user

@pytest.fixture
def customer_user(db):
    user = User.objects.create_user(username="customer_test", password="pw12345", role="customer")
    return user

@pytest.fixture
def offer_data():
    return {
        "title": "Grafikdesign-Paket",
        "image": None,
        "description": "Ein umfassendes Grafikdesign-Paket für Unternehmen.",
        "details": [
            {
                "title": "Basic Design",
                "revisions": 2,
                "delivery_time_in_days": 5,
                "price": 100,
                "features": ["Logo Design", "Visitenkarte"],
                "offer_type": "basic"
            },
            {
                "title": "Standard Design",
                "revisions": 5,
                "delivery_time_in_days": 7,
                "price": 200,
                "features": ["Logo Design", "Visitenkarte", "Briefpapier"],
                "offer_type": "standard"
            },
            {
                "title": "Premium Design",
                "revisions": 10,
                "delivery_time_in_days": 10,
                "price": 500,
                "features": ["Logo Design", "Visitenkarte", "Briefpapier", "Flyer"],
                "offer_type": "premium"
            }
        ]
    }

@pytest.mark.django_db
def test_offer_list_returns_200():
    """
    Tests if GET /api/offers/ returns HTTP 200.
    """
    client = APIClient()
    url = reverse('offer-list-create')
    response = client.get(url)
    assert response.status_code == 200

@pytest.mark.django_db
def test_offer_list_pagination_and_fields():
    """
    Tests if offer list returns correct fields and pagination.
    """
    user = User.objects.create(username="john")
    offer = Offer.objects.create(
        user=user,
        title="Test Offer",
        description="Description",
        min_price=50,
        min_delivery_time=5,
    )

    OfferDetail.objects.create(
        offer=offer,
        title="Basic Design",
        revisions=1,
        delivery_time_in_days=5,
        price=20,
        features=["Feature A"],
        offer_type="basic"
    )
    client = APIClient()
    url = reverse('offer-list-create')
    response = client.get(url)
    data = response.json()
    assert "results" in data
    assert data["results"][0]["title"] == "Test Offer"
    assert "details" in data["results"][0]

@pytest.mark.django_db
def test_offer_filter_by_min_price():
    """
    Tests offer list filtering by min_price.
    """
    user = User.objects.create(username="john")
    Offer.objects.create(
        user=user,
        title="Cheap Offer",
        description="desc",
        min_price=10,
        min_delivery_time=3,
    )
    Offer.objects.create(
        user=user,
        title="Expensive Offer",
        description="desc",
        min_price=100,
        min_delivery_time=3,
    )
    client = APIClient()
    url = reverse('offer-list-create')
    response = client.get(url + "?min_price=50")
    data = response.json()
    assert all(
        Decimal(offer["min_price"]) >= 50 for offer in data["results"]
    )

@pytest.mark.django_db
def test_offers_list_success():
    """
    GET /api/offers/ returns status 200 and a paginated list with offer details.
    """
    user = User.objects.create(username="jdoe", first_name="John", last_name="Doe")
    offer = Offer.objects.create(
        user=user,
        title="Website Design",
        description="Professionelles Website-Design...",
        min_price=100,
        min_delivery_time=7,
    )

    OfferDetail.objects.create(
        offer=offer,
        title="Basic Design",
        revisions=2,
        delivery_time_in_days=5,
        price=100,
        features=["Logo Design", "Visitenkarte"],
        offer_type="basic",
    )
    OfferDetail.objects.create(
        offer=offer,
        title="Standard Design",
        revisions=5,
        delivery_time_in_days=7,
        price=200,
        features=["Logo Design", "Visitenkarte", "Briefpapier"],
        offer_type="standard",
    )
    OfferDetail.objects.create(
        offer=offer,
        title="Premium Design",
        revisions=10,
        delivery_time_in_days=10,
        price=500,
        features=["Logo Design", "Visitenkarte", "Briefpapier", "Flyer"],
        offer_type="premium",
    )
    client = APIClient()
    url = reverse('offer-list-create')
    response = client.get(url)
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert data["results"][0]["title"] == "Website Design"
    assert Decimal(data["results"][0]["min_price"]) == Decimal("100.00")
    assert data["results"][0]["min_delivery_time"] == 7
    assert data["results"][0]["user_details"]["first_name"] == "John"
    assert len(data["results"][0]["details"]) == 3

@pytest.mark.django_db
def test_offers_list_invalid_parameter():
    """
    GET /api/offers/?min_price=abc returns status 400 for invalid parameter.
    """
    client = APIClient()
    url = reverse('offer-list-create')
    response = client.get(url + "?min_price=abc")
    assert response.status_code == 400

@pytest.mark.django_db
def test_offer_post_201_success(business_user, offer_data):
    """
    201: Offer is created by a business user with valid data.
    """
    client = APIClient()
    client.force_authenticate(user=business_user)
    url = reverse('offer-list-create')
    response = client.post(url, offer_data, format='json')
    assert response.status_code == 201
    assert response.data["title"] == offer_data["title"]
    assert len(response.data["details"]) == 3

import copy

@pytest.mark.django_db
def test_offer_post_400_less_than_3_details(business_user, offer_data):
    """
    400: Less than 3 offer details returns error.
    """
    client = APIClient()
    client.force_authenticate(user=business_user)
    url = reverse('offer-list-create')
    data = copy.deepcopy(offer_data)
    data["details"] = [data["details"][0]]  # only 1 detail
    response = client.post(url, data, format='json')
    assert response.status_code == 400
    assert "At least 3 offer details are required." in str(response.data)

@pytest.mark.django_db
def test_offer_post_401_unauthenticated(offer_data):
    """
    401: Unauthenticated user cannot create offer.
    """
    client = APIClient()
    url = reverse('offer-list-create')
    response = client.post(url, offer_data, format='json')
    assert response.status_code == 401
    assert "credentials" in str(response.data).lower()

@pytest.mark.django_db
def test_offer_post_403_non_business(customer_user, offer_data):
    """
    403: Customer user cannot create offer.
    """
    client = APIClient()
    client.force_authenticate(user=customer_user)
    url = reverse('offer-list-create')
    response = client.post(url, offer_data, format='json')
    assert response.status_code == 403
    assert "permission" in str(response.data).lower()
    
@pytest.mark.django_db
def test_offer_detail_200_success(business_user):
    """
    200: Authenticated user can fetch offer details by id.
    """
    offer = Offer.objects.create(user=business_user, title="Detail", description="Test")
    client = APIClient()
    client.force_authenticate(user=business_user)
    url = reverse('offer-detail', args=[offer.id])
    response = client.get(url)
    assert response.status_code == 200
    assert response.data["id"] == offer.id

@pytest.mark.django_db
def test_offer_detail_401_unauthenticated(business_user):
    """
    401: Unauthenticated user cannot fetch offer detail.
    """
    offer = Offer.objects.create(user=business_user, title="Detail", description="Test")
    client = APIClient()
    url = reverse('offer-detail', args=[offer.id])
    response = client.get(url)
    assert response.status_code == 401

@pytest.mark.django_db
def test_offer_detail_404_not_found(business_user):
    """
    404: Offer with given ID does not exist.
    """
    client = APIClient()
    client.force_authenticate(user=business_user)
    url = reverse('offer-detail', args=[999999])
    response = client.get(url)
    assert response.status_code == 404

@pytest.mark.django_db
def test_offer_patch_200_success(business_user):
    """
    200: Owner can PATCH their offer.
    """
    offer = Offer.objects.create(user=business_user, title="Old", description="Old")
    client = APIClient()
    client.force_authenticate(user=business_user)
    url = reverse('offer-detail', args=[offer.id])
    data = {"title": "Updated"}
    response = client.patch(url, data, format="json")
    assert response.status_code == 200
    offer.refresh_from_db()
    assert offer.title == "Updated"

@pytest.mark.django_db
def test_offer_patch_400_invalid(business_user):
    """
    400: PATCH with invalid data returns 400.
    """
    offer = Offer.objects.create(user=business_user, title="Old", description="Old")
    client = APIClient()
    client.force_authenticate(user=business_user)
    url = reverse('offer-detail', args=[offer.id])
    data = {"title": None}  # or other invalid data
    response = client.patch(url, data, format="json")
    assert response.status_code == 400

@pytest.mark.django_db
def test_offer_patch_401_unauthenticated(business_user):
    """
    401: PATCH without authentication returns 401.
    """
    offer = Offer.objects.create(user=business_user, title="Old", description="Old")
    client = APIClient()
    url = reverse('offer-detail', args=[offer.id])
    data = {"title": "Test"}
    response = client.patch(url, data, format="json")
    assert response.status_code == 401

@pytest.mark.django_db
def test_offer_patch_403_not_owner(business_user, customer_user):
    """
    403: Non-owner cannot PATCH offer.
    """
    offer = Offer.objects.create(user=business_user, title="Old", description="Old")
    client = APIClient()
    client.force_authenticate(user=customer_user)
    url = reverse('offer-detail', args=[offer.id])
    data = {"title": "Hack"}
    response = client.patch(url, data, format="json")
    assert response.status_code == 403

@pytest.mark.django_db
def test_offer_patch_404_not_found(business_user):
    """
    404: PATCH to non-existent offer.
    """
    client = APIClient()
    client.force_authenticate(user=business_user)
    url = reverse('offer-detail', args=[999999])
    data = {"title": "Nope"}
    response = client.patch(url, data, format="json")
    assert response.status_code == 404

@pytest.mark.django_db
class TestOfferDeleteAPI:
    @pytest.fixture
    def owner(self, django_user_model):
        return django_user_model.objects.create_user(username="owner", password="test123", role="business")

    @pytest.fixture
    def other_user(self, django_user_model):
        return django_user_model.objects.create_user(username="other", password="test123", role="business")

    @pytest.fixture
    def offer(self, owner):
        from offers_app.models import Offer
        return Offer.objects.create(
            user=owner,
            title="Test-Angebot",
            description="Beschreibung",
        )

    @pytest.fixture
    def api_client(self):
        return APIClient()

    def test_delete_offer_unauthenticated(self, api_client, offer):
        """DELETE should fail with 401 if not authenticated."""
        url = reverse("offer-detail", args=[offer.id])
        response = api_client.delete(url)
        assert response.status_code == 401

    def test_delete_offer_forbidden_for_non_owner(self, api_client, offer, other_user):
        """DELETE should fail with 403 if user is not owner."""
        api_client.force_authenticate(user=other_user)
        url = reverse("offer-detail", args=[offer.id])
        response = api_client.delete(url)
        assert response.status_code == 403

    def test_delete_offer_success_for_owner(self, api_client, offer, owner):
        """DELETE should succeed with 204 for owner."""
        api_client.force_authenticate(user=owner)
        url = reverse("offer-detail", args=[offer.id])
        response = api_client.delete(url)
        assert response.status_code == 204

    def test_delete_offer_not_found(self, api_client, owner):
        """DELETE should fail with 404 if offer does not exist."""
        api_client.force_authenticate(user=owner)
        url = reverse("offer-detail", args=[9999])  # Very high, does not exist
        response = api_client.delete(url)
        assert response.status_code == 404

@pytest.mark.django_db
class TestOfferDetailRetrieveAPI:
    @pytest.fixture
    def user(self, django_user_model):
        return django_user_model.objects.create_user(username="basic", password="test123")

    @pytest.fixture
    def offer(self, user):
        from offers_app.models import Offer
        return Offer.objects.create(
            user=user,
            title="Some Offer",
            description="Beschreibung",
        )

    @pytest.fixture
    def offer_detail(self, offer):
        from offers_app.models import OfferDetail
        return OfferDetail.objects.create(
            offer=offer,
            title="Basic Design",
            revisions=2,
            delivery_time_in_days=5,
            price=100,
            features=["Logo Design", "Visitenkarte"],
            offer_type="basic",
        )

    @pytest.fixture
    def api_client(self):
        return APIClient()

    def test_retrieve_offerdetail_authenticated(self, api_client, user, offer_detail):
        """GET should return 200 and detail data if authenticated."""
        api_client.force_authenticate(user=user)
        url = reverse("offerdetail-detail", args=[offer_detail.id])
        response = api_client.get(url)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == offer_detail.id
        assert data["title"] == "Basic Design"
        assert data["revisions"] == 2
        assert data["delivery_time_in_days"] == 5
        assert float(data["price"]) == 100.0
        assert data["features"] == ["Logo Design", "Visitenkarte"]
        assert data["offer_type"] == "basic"

    def test_retrieve_offerdetail_unauthenticated(self, api_client, offer_detail):
        """GET should fail with 401 if not authenticated."""
        url = reverse("offerdetail-detail", args=[offer_detail.id])
        response = api_client.get(url)
        assert response.status_code == 401

    def test_retrieve_offerdetail_not_found(self, api_client, user):
        """GET should fail with 404 if offer detail does not exist."""
        api_client.force_authenticate(user=user)
        url = reverse("offerdetail-detail", args=[9999])
        response = api_client.get(url)
        assert response.status_code == 404

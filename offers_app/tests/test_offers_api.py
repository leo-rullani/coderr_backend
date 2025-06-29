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
    OfferDetail.objects.create(offer=offer, url="/offerdetails/1/")
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
    OfferDetail.objects.create(offer=offer, url="/offerdetails/1/")
    OfferDetail.objects.create(offer=offer, url="/offerdetails/2/")
    OfferDetail.objects.create(offer=offer, url="/offerdetails/3/")
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

@pytest.mark.django_db
def test_offer_post_400_less_than_3_details(business_user, offer_data):
    """
    400: Less than 3 offer details returns error.
    """
    client = APIClient()
    client.force_authenticate(user=business_user)
    url = reverse('offer-list-create')
    offer_data["details"] = [offer_data["details"][0]]  # only 1 detail
    response = client.post(url, offer_data, format='json')
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
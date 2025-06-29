import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from offers_app.models import Offer, OfferDetail
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()

@pytest.mark.django_db
def test_offer_list_returns_200():
    """
    Tests if GET /api/offers/ returns HTTP 200.
    """
    client = APIClient()
    url = reverse('offer-list')
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
    url = reverse('offer-list')
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
    url = reverse('offer-list')
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
    url = reverse('offer-list')
    response = client.get(url)
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert data["results"][0]["title"] == "Website Design"
    # Vergleiche als Decimal für Korrektheit
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
    url = reverse('offer-list')
    response = client.get(url + "?min_price=abc")
    assert response.status_code == 400
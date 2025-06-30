import pytest
from rest_framework.test import APIClient
from django.urls import reverse

@pytest.mark.django_db
class TestOrderAPI:
    @pytest.fixture
    def customer(self, django_user_model):
        return django_user_model.objects.create_user(username="kunde", password="test123")

    @pytest.fixture
    def business(self, django_user_model):
        return django_user_model.objects.create_user(username="firma", password="test123")

    @pytest.fixture
    def order(self, customer, business):
        from orders_app.models import Order
        return Order.objects.create(
            customer_user=customer,
            business_user=business,
            title="Logo Design",
            revisions=3,
            delivery_time_in_days=5,
            price=150,
            features=["Logo Design", "Visitenkarten"],
            offer_type="basic",
            status="in_progress"
        )

    @pytest.fixture
    def api_client(self):
        return APIClient()
    
    def test_list_orders_authenticated(self, api_client, customer, order):
        api_client.force_authenticate(user=customer)
        url = reverse("order-list-create")
        response = api_client.get(url)
        print("Status:", response.status_code, "Data:", response.json())  # Debug
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "results" in data
        assert any(o["id"] == order.id for o in data["results"])


    def test_list_orders_unauthenticated(self, api_client):
        url = reverse("order-list-create")
        response = api_client.get(url)
        assert response.status_code == 401

    def test_retrieve_order_authenticated(self, api_client, customer, order):
        api_client.force_authenticate(user=customer)
        url = reverse("order-detail", args=[order.id])
        response = api_client.get(url)
        assert response.status_code == 200
        assert response.json()["id"] == order.id

    def test_retrieve_order_unauthenticated(self, api_client, order):
        url = reverse("order-detail", args=[order.id])
        response = api_client.get(url)
        assert response.status_code == 401

    def test_create_order(self, api_client, customer, business):
        api_client.force_authenticate(user=customer)
        url = reverse("order-list-create")
        payload = {
            "customer_user": customer.id,
            "business_user": business.id,
            "title": "Neue Bestellung",
            "revisions": 2,
            "delivery_time_in_days": 3,
            "price": 100,
            "features": ["Logo", "Briefpapier"],
            "offer_type": "basic",
            "status": "in_progress"
        }
        response = api_client.post(url, payload, format="json")
        assert response.status_code in (201, 200)
        assert response.json()["title"] == "Neue Bestellung"
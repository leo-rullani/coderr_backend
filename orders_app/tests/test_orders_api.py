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
@pytest.mark.django_db
class TestOrderStatusPatch:
    @pytest.fixture
    def customer(self, django_user_model):
        return django_user_model.objects.create_user(username="kunde", password="test123", role="customer")

    @pytest.fixture
    def business(self, django_user_model):
        return django_user_model.objects.create_user(username="firma", password="test123", role="business")

    @pytest.fixture
    def order(self, customer, business):
        from orders_app.models import Order
        return Order.objects.create(
            customer_user=customer,
            business_user=business,
            title="Patch Test",
            revisions=2,
            delivery_time_in_days=7,
            price=99,
            features=["Patch"],
            offer_type="basic",
            status="in_progress"
        )

@pytest.fixture
def offer_detail(customer, business):
    from offers_app.models import Offer, OfferDetail
    offer = Offer.objects.create(
        user=business,
        title="Testangebot",
        description="desc",
        min_price=50,
        min_delivery_time=3,
    )
    return OfferDetail.objects.create(
        offer=offer,
        title="Basic Design",
        revisions=1,
        delivery_time_in_days=5,
        price=20,
        features=["Feature A"],
        offer_type="basic"
    )

@pytest.mark.django_db
class TestOrderAPI:
    @pytest.fixture
    def customer(self, django_user_model):
        return django_user_model.objects.create_user(username="kunde", password="test123", role="customer")

    @pytest.fixture
    def business(self, django_user_model):
        return django_user_model.objects.create_user(username="firma", password="test123", role="business")

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

    def test_create_order(self, api_client, customer, offer_detail):
        """
        POST /api/orders/ - create order from offer_detail_id (only customers allowed)
        """
        api_client.force_authenticate(user=customer)
        url = reverse("order-list-create")
        payload = {"offer_detail_id": offer_detail.id}
        response = api_client.post(url, payload, format="json")
        assert response.status_code in (201, 200)
        assert response.json()["title"] == offer_detail.title

    def test_patch_status_success(self, api_client, business, order):
        """
        PATCH /api/orders/{id}/ - success for business_user, status updated
        """
        api_client.force_authenticate(user=business)
        url = reverse("order-detail", args=[order.id])
        response = api_client.patch(url, {"status": "completed"}, format="json")
        assert response.status_code == 200
        assert response.json()["status"] == "completed"

    def test_patch_status_invalid_status(self, api_client, business, order):
        """
        PATCH /api/orders/{id}/ - 400 for invalid status value
        """
        api_client.force_authenticate(user=business)
        url = reverse("order-detail", args=[order.id])
        response = api_client.patch(url, {"status": "INVALID"}, format="json")
        assert response.status_code == 400
        # Standard-DRF-Error: '"INVALID" is not a valid choice.'
        assert "not a valid choice" in str(response.data["status"][0])

    def test_patch_status_forbidden_for_customer(self, api_client, customer, order):
        """
        PATCH /api/orders/{id}/ - 403 for customer (not business_user)
        """
        api_client.force_authenticate(user=customer)
        url = reverse("order-detail", args=[order.id])
        response = api_client.patch(url, {"status": "completed"}, format="json")
        assert response.status_code == 403

    def test_patch_status_forbidden_for_other_business(self, api_client, django_user_model, order):
        """
        PATCH /api/orders/{id}/ - 403 for other business user
        """
        other_business = django_user_model.objects.create_user(username="anderefirma", password="test123", role="business")
        api_client.force_authenticate(user=other_business)
        url = reverse("order-detail", args=[order.id])
        response = api_client.patch(url, {"status": "completed"}, format="json")
        assert response.status_code == 403

    def test_patch_status_unauthenticated(self, api_client, order):
        """
        PATCH /api/orders/{id}/ - 401 for unauthenticated
        """
        url = reverse("order-detail", args=[order.id])
        response = api_client.patch(url, {"status": "completed"}, format="json")
        assert response.status_code == 401

    def test_patch_status_not_found(self, api_client, business):
        """
        PATCH /api/orders/99999/ - 404 for non-existing order
        """
        api_client.force_authenticate(user=business)
        url = reverse("order-detail", args=[99999])
        response = api_client.patch(url, {"status": "completed"}, format="json")
        assert response.status_code == 404

    def test_patch_status_extra_field(self, api_client, business, order):
        """
        PATCH /api/orders/{id}/ - 400 if any other field except status is sent
        """
        api_client.force_authenticate(user=business)
        url = reverse("order-detail", args=[order.id])
        response = api_client.patch(url, {"status": "completed", "title": "hacked"}, format="json")
        assert response.status_code == 400

@pytest.mark.django_db
class TestOrderDeleteAPI:
    @pytest.fixture
    def admin(self, django_user_model):
        return django_user_model.objects.create_user(
            username="admin", password="test123", is_staff=True
        )

    @pytest.fixture
    def customer(self, django_user_model):
        return django_user_model.objects.create_user(
            username="kunde", password="test123", role="customer"
        )

    @pytest.fixture
    def business(self, django_user_model):
        return django_user_model.objects.create_user(
            username="firma", password="test123", role="business"
        )

    @pytest.fixture
    def order(self, customer, business):
        from orders_app.models import Order
        return Order.objects.create(
            customer_user=customer,
            business_user=business,
            title="Patch Test",
            revisions=1,
            delivery_time_in_days=2,
            price=99,
            features=["f1"],
            offer_type="basic",
            status="in_progress"
        )

    @pytest.fixture
    def api_client(self):
        return APIClient()

    def test_delete_order_success_for_admin(self, api_client, admin, order):
        """
        DELETE /api/orders/{id}/ - success for admin user
        """
        api_client.force_authenticate(user=admin)
        url = reverse("order-detail", args=[order.id])
        response = api_client.delete(url)
        assert response.status_code == 204

    def test_delete_order_forbidden_for_customer(self, api_client, customer, order):
        """
        DELETE /api/orders/{id}/ - 403 for customer
        """
        api_client.force_authenticate(user=customer)
        url = reverse("order-detail", args=[order.id])
        response = api_client.delete(url)
        assert response.status_code == 403

    def test_delete_order_unauthenticated(self, api_client, order):
        """
        DELETE /api/orders/{id}/ - 401 for unauthenticated
        """
        url = reverse("order-detail", args=[order.id])
        response = api_client.delete(url)
        assert response.status_code == 401

    def test_delete_order_not_found(self, api_client, admin):
        """
        DELETE /api/orders/99999/ - 404 for non-existing order
        """
        api_client.force_authenticate(user=admin)
        url = reverse("order-detail", args=[99999])
        response = api_client.delete(url)
        assert response.status_code == 404

@pytest.mark.django_db
class TestOrderCountAPI:

    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def business(self, django_user_model):
        return django_user_model.objects.create_user(username="firma", password="test123", role="business")

    @pytest.fixture
    def customer(self, django_user_model):
        return django_user_model.objects.create_user(username="kunde", password="test123", role="customer")

    @pytest.fixture
    def create_orders(self, business, customer):
        from orders_app.models import Order
        for _ in range(3):
            Order.objects.create(
                customer_user=customer,
                business_user=business,
                title="Order Test",
                revisions=1,
                delivery_time_in_days=3,
                price=100,
                features=["Test"],
                offer_type="basic",
                status="in_progress",
            )
            
        Order.objects.create(
            customer_user=customer,
            business_user=business,
            title="Abgeschlossen",
            revisions=1,
            delivery_time_in_days=3,
            price=100,
            features=["Test"],
            offer_type="basic",
            status="completed",
        )

    def test_order_count_success(self, api_client, business, create_orders):
        """
        GET /api/order-count/{business_user_id}/ - returns correct count
        """
        api_client.force_authenticate(user=business)
        url = reverse("order-count", args=[business.id])
        response = api_client.get(url)
        assert response.status_code == 200
        assert response.json()["order_count"] == 3

    def test_order_count_unauthenticated(self, api_client, business):
        """
        GET /api/order-count/{business_user_id}/ - 401 if not authenticated
        """
        url = reverse("order-count", args=[business.id])
        response = api_client.get(url)
        assert response.status_code == 401

    def test_order_count_user_not_found(self, api_client, business):
        """
        GET /api/order-count/99999/ - 404 for missing business user
        """
        api_client.force_authenticate(user=business)
        url = reverse("order-count", args=[99999])
        response = api_client.get(url)
        assert response.status_code == 404
@pytest.mark.django_db
class TestCompletedOrderCountAPI:
    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def business(self, django_user_model):
        return django_user_model.objects.create_user(username="firma", password="test123", role="business")

    @pytest.fixture
    def customer(self, django_user_model):
        return django_user_model.objects.create_user(username="kunde", password="test123", role="customer")

    @pytest.fixture
    def completed_orders(self, business, customer):
        
        from orders_app.models import Order
        for _ in range(3):
            Order.objects.create(
                customer_user=customer,
                business_user=business,
                title="Done",
                revisions=1,
                delivery_time_in_days=1,
                price=10,
                features=[],
                offer_type="basic",
                status="completed",
            )
        for _ in range(2):
            Order.objects.create(
                customer_user=customer,
                business_user=business,
                title="WIP",
                revisions=1,
                delivery_time_in_days=1,
                price=10,
                features=[],
                offer_type="basic",
                status="in_progress",
            )

    def test_completed_order_count_success(self, api_client, business, completed_orders):
        """
        GET /api/completed-order-count/{business_user_id}/ - returns correct count for completed orders
        """
        api_client.force_authenticate(user=business)
        url = reverse("completed-order-count", args=[business.id])
        response = api_client.get(url)
        assert response.status_code == 200
        assert response.json() == {"completed_order_count": 3}

    def test_completed_order_count_unauthenticated(self, api_client, business, completed_orders):
        """
        GET /api/completed-order-count/{business_user_id}/ - 401 for unauthenticated
        """
        url = reverse("completed-order-count", args=[business.id])
        response = api_client.get(url)
        assert response.status_code == 401

    def test_completed_order_count_user_not_found(self, api_client, business):
        """
        GET /api/completed-order-count/99999/ - 404 for missing business user
        """
        api_client.force_authenticate(user=business)
        url = reverse("completed-order-count", args=[99999])
        response = api_client.get(url)
        assert response.status_code == 404
        assert response.json()["detail"] == "Business user not found."
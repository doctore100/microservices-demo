import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def seed_products(fake_redis):
    fake_redis._store["products:valid"] = {
        "p-test",
        "dup-test",
        "get-me",
        "aaa",
        "bbb",
        "upd-test",
        "del-test",
    }


class TestRoot:
    def test_root(self):
        resp = client.get("/")
        assert resp.status_code == 200
        assert resp.json() == {"message": "Hello World --> 2"}


class TestCreateOrder:
    def test_create_order(self):
        resp = client.post(
            "/orders",
            json={
                "product_id": "p-test",
                "price": 100.0,
                "fee": 15.0,
                "total": 115.0,
                "quantity": 2,
                "status": "PENDING",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["product_id"] == "p-test"
        assert data["status"] == "PENDING"

    def test_create_duplicate_returns_409(self):
        client.post(
            "/orders",
            json={
                "product_id": "dup-test",
                "price": 1.0,
                "fee": 0.1,
                "total": 1.1,
                "quantity": 1,
                "status": "PENDING",
            },
        )
        resp = client.post(
            "/orders",
            json={
                "product_id": "dup-test",
                "price": 2.0,
                "fee": 0.2,
                "total": 2.2,
                "quantity": 2,
                "status": "COMPLETE",
            },
        )
        assert resp.status_code == 409
        assert "dup-test" in resp.json()["detail"]


class TestGetOrder:
    def test_get_existing(self):
        client.post(
            "/orders",
            json={
                "product_id": "get-me",
                "price": 5.0,
                "fee": 0.5,
                "total": 5.5,
                "quantity": 1,
                "status": "PENDING",
            },
        )
        resp = client.get("/orders/get-me")
        assert resp.status_code == 200
        assert resp.json()["product_id"] == "get-me"
        assert resp.json()["status"] == "PENDING"

    def test_get_missing_returns_404(self):
        resp = client.get("/orders/nobody")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Order not found"


class TestListOrders:
    def test_list_orders(self):
        client.post(
            "/orders",
            json={
                "product_id": "aaa",
                "price": 1.0,
                "fee": 0.1,
                "total": 1.1,
                "quantity": 1,
                "status": "PENDING",
            },
        )
        client.post(
            "/orders",
            json={
                "product_id": "bbb",
                "price": 2.0,
                "fee": 0.2,
                "total": 2.2,
                "quantity": 2,
                "status": "COMPLETE",
            },
        )
        resp = client.get("/orders")
        assert resp.status_code == 200
        assert resp.json() == ["aaa", "bbb"]


class TestUpdateOrderStatus:
    def test_update_status_existing(self):
        client.post(
            "/orders",
            json={
                "product_id": "upd-test",
                "price": 5.0,
                "fee": 0.5,
                "total": 5.5,
                "quantity": 1,
                "status": "PENDING",
            },
        )
        resp = client.put("/orders/upd-test", json={"status": "COMPLETE"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "COMPLETE"
        assert resp.json()["product_id"] == "upd-test"

    def test_update_missing_returns_404(self):
        resp = client.put("/orders/nobody", json={"status": "COMPLETE"})
        assert resp.status_code == 404


class TestDeleteOrder:
    def test_delete_existing(self):
        client.post(
            "/orders",
            json={
                "product_id": "del-test",
                "price": 3.0,
                "fee": 0.3,
                "total": 3.3,
                "quantity": 1,
                "status": "PENDING",
            },
        )
        resp = client.delete("/orders/del-test")
        assert resp.status_code == 200
        assert resp.json() == {"message": "Order for product 'del-test' deleted"}

        get_resp = client.get("/orders/del-test")
        assert get_resp.status_code == 404

    def test_delete_missing_returns_404(self):
        resp = client.delete("/orders/nobody")
        assert resp.status_code == 404

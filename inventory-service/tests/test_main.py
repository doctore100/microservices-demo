from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestRoot:
    def test_root(self):
        resp = client.get("/")
        assert resp.status_code == 200
        assert resp.json() == {"message": "Hello World --> 1"}


class TestCreateProduct:
    def test_create_product(self):
        resp = client.post(
            "/products", json={"name": "p-test", "price": 15.0, "quantity": 2}
        )
        assert resp.status_code == 200
        assert resp.json() == {"name": "p-test", "price": 15.0, "quantity": 2}

    def test_create_duplicate_returns_409(self):
        client.post("/products", json={"name": "dup-test", "price": 1.0, "quantity": 1})
        resp = client.post(
            "/products", json={"name": "dup-test", "price": 2.0, "quantity": 2}
        )
        assert resp.status_code == 409
        assert "dup-test" in resp.json()["detail"]


class TestGetProduct:
    def test_get_existing(self):
        client.post("/products", json={"name": "get-me", "price": 5.0, "quantity": 1})
        resp = client.get("/products/get-me")
        assert resp.status_code == 200
        assert resp.json()["name"] == "get-me"

    def test_get_missing_returns_404(self):
        resp = client.get("/products/nobody")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Product not found"


class TestListProducts:
    def test_list_products(self):
        client.post("/products", json={"name": "aaa", "price": 1.0, "quantity": 1})
        client.post("/products", json={"name": "bbb", "price": 2.0, "quantity": 2})
        resp = client.get("/products")
        assert resp.status_code == 200
        assert resp.json() == ["aaa", "bbb"]


class TestUpdateProduct:
    def test_update_existing(self):
        client.post("/products", json={"name": "upd-test", "price": 5.0, "quantity": 1})
        resp = client.put("/products/upd-test", json={"price": 20.0, "quantity": 10})
        assert resp.status_code == 200
        assert resp.json() == {"name": "upd-test", "price": 20.0, "quantity": 10}

    def test_update_missing_returns_404(self):
        resp = client.put("/products/nobody", json={"price": 1.0, "quantity": 1})
        assert resp.status_code == 404


class TestDeleteProduct:
    def test_delete_existing(self):
        client.post("/products", json={"name": "del-test", "price": 3.0, "quantity": 1})
        resp = client.delete("/products/del-test")
        assert resp.status_code == 200
        assert resp.json() == {"message": "Product 'del-test' deleted"}

        get_resp = client.get("/products/del-test")
        assert get_resp.status_code == 404

    def test_delete_missing_returns_404(self):
        resp = client.delete("/products/nobody")
        assert resp.status_code == 404

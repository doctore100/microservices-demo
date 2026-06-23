from fastapi.testclient import TestClient

from app.consumer import _process_product_event
from app.main import app

client = TestClient(app)


class TestCreateOrderValidatesProduct:
    def test_create_order_product_not_found(self):
        resp = client.post(
            "/orders",
            json={
                "product_id": "ghost-product",
                "price": 100.0,
                "fee": 15.0,
                "total": 115.0,
                "quantity": 2,
                "status": "PENDING",
            },
        )
        assert resp.status_code == 400
        assert "ghost-product" in resp.json()["detail"]

    def test_create_order_with_existing_product_succeeds(self, fake_redis):
        fake_redis._store["products:valid"] = {"existing-prod"}
        resp = client.post(
            "/orders",
            json={
                "product_id": "existing-prod",
                "price": 50.0,
                "fee": 5.0,
                "total": 55.0,
                "quantity": 1,
                "status": "PENDING",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["product_id"] == "existing-prod"

    def test_create_order_with_existing_key_fallback(self, fake_redis):
        fake_redis._store["product:key-fallback"] = {
            "name": "key-fallback",
            "price": 10.0,
            "quantity": 3,
        }
        resp = client.post(
            "/orders",
            json={
                "product_id": "key-fallback",
                "price": 10.0,
                "fee": 1.0,
                "total": 11.0,
                "quantity": 1,
                "status": "PENDING",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["product_id"] == "key-fallback"


class TestPublishOrderEvents:
    def test_create_order_publishes_created_event(self, fake_redis):
        fake_redis._store["products:valid"] = {"pub-test"}
        client.post(
            "/orders",
            json={
                "product_id": "pub-test",
                "price": 10.0,
                "fee": 1.0,
                "total": 11.0,
                "quantity": 1,
                "status": "PENDING",
            },
        )
        stream = fake_redis._streams.get("order:events", [])
        assert len(stream) >= 1
        event_types = [data["event"] for _, data in stream]
        assert "order.created" in event_types

    def test_update_to_complete_publishes_completed_event(self, fake_redis):
        fake_redis._store["products:valid"] = {"complete-test"}
        fake_redis._store["order:complete-test"] = {
            "product_id": "complete-test",
            "price": 10.0,
            "fee": 1.0,
            "total": 11.0,
            "quantity": 1,
            "status": "PENDING",
        }
        fake_redis._streams.clear()
        resp = client.put("/orders/complete-test", json={"status": "COMPLETE"})
        assert resp.status_code == 200

        stream = fake_redis._streams.get("order:events", [])
        assert any(data["event"] == "order.completed" for _, data in stream)

    def test_update_to_refunded_publishes_refunded_event(self, fake_redis):
        fake_redis._store["products:valid"] = {"refund-test"}
        fake_redis._store["order:refund-test"] = {
            "product_id": "refund-test",
            "price": 10.0,
            "fee": 1.0,
            "total": 11.0,
            "quantity": 1,
            "status": "COMPLETE",
        }
        fake_redis._streams.clear()
        resp = client.put("/orders/refund-test", json={"status": "REFUNDED"})
        assert resp.status_code == 200

        stream = fake_redis._streams.get("order:events", [])
        assert any(data["event"] == "order.refunded" for _, data in stream)

    def test_delete_order_publishes_deleted_event(self, fake_redis):
        fake_redis._store["products:valid"] = {"del-event-test"}
        fake_redis._store["order:del-event-test"] = {
            "product_id": "del-event-test",
            "price": 10.0,
            "fee": 1.0,
            "total": 11.0,
            "quantity": 1,
            "status": "PENDING",
        }
        fake_redis._streams.clear()
        resp = client.delete("/orders/del-event-test")
        assert resp.status_code == 200

        stream = fake_redis._streams.get("order:events", [])
        assert any(data["event"] == "order.deleted" for _, data in stream)


class TestConsumeProductEvents:
    async def test_created_adds_to_valid_set(self, fake_redis):
        await _process_product_event(
            {
                "event": "product.created",
                "name": "new-prod",
            }
        )
        assert await fake_redis.sismember("products:valid", "new-prod") == 1

    async def test_deleted_removes_from_valid_set(self, fake_redis):
        await fake_redis.sadd("products:valid", "goner")
        await _process_product_event(
            {
                "event": "product.deleted",
                "name": "goner",
            }
        )
        assert await fake_redis.sismember("products:valid", "goner") == 0

    async def test_deleted_refunds_pending_order(self, fake_redis):
        fake_redis._store["order:to-refund"] = {
            "product_id": "to-refund",
            "price": 30.0,
            "fee": 3.0,
            "total": 33.0,
            "quantity": 1,
            "status": "PENDING",
        }
        await _process_product_event(
            {
                "event": "product.deleted",
                "name": "to-refund",
            }
        )
        updated = await fake_redis.json().get("order:to-refund")
        assert updated["status"] == "REFUNDED"

    async def test_deleted_does_not_refund_completed_order(self, fake_redis):
        fake_redis._store["order:keep"] = {
            "product_id": "keep",
            "price": 30.0,
            "fee": 3.0,
            "total": 33.0,
            "quantity": 1,
            "status": "COMPLETE",
        }
        await _process_product_event(
            {
                "event": "product.deleted",
                "name": "keep",
            }
        )
        updated = await fake_redis.json().get("order:keep")
        assert updated["status"] == "COMPLETE"

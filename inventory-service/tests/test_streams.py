from fastapi.testclient import TestClient

from app.consumer import _process_order_event
from app.main import app

client = TestClient(app)


class TestPublishProductCreated:
    def test_create_product_adds_stream_event(self, fake_redis):
        resp = client.post(
            "/products", json={"name": "stream-test", "price": 10.0, "quantity": 5}
        )
        assert resp.status_code == 200

        stream = fake_redis._streams.get("product:events", [])
        assert len(stream) == 1
        msg_id, data = stream[0]
        assert data["event"] == "product.created"
        assert data["name"] == "stream-test"


class TestPublishProductDeleted:
    def test_delete_product_adds_stream_event(self, fake_redis):
        client.post(
            "/products", json={"name": "del-event", "price": 1.0, "quantity": 1}
        )

        fake_redis._streams.clear()
        resp = client.delete("/products/del-event")
        assert resp.status_code == 200

        stream = fake_redis._streams.get("product:events", [])
        assert len(stream) == 1
        msg_id, data = stream[0]
        assert data["event"] == "product.deleted"
        assert data["name"] == "del-event"


class TestConsumeOrderCompleted:
    async def test_decrements_stock(self, fake_redis):
        fake_redis._store["product:widget"] = {
            "name": "widget",
            "price": 5.0,
            "quantity": 10,
        }
        await _process_order_event(
            {
                "event": "order.completed",
                "product_id": "widget",
                "quantity": "3",
            }
        )
        assert fake_redis._store["product:widget"]["quantity"] == 7

    async def test_refund_increments_stock(self, fake_redis):
        fake_redis._store["product:gadget"] = {
            "name": "gadget",
            "price": 20.0,
            "quantity": 5,
        }
        await _process_order_event(
            {
                "event": "order.refunded",
                "product_id": "gadget",
                "quantity": "2",
            }
        )
        assert fake_redis._store["product:gadget"]["quantity"] == 7

    async def test_missing_product_does_nothing(self, fake_redis):
        await _process_order_event(
            {
                "event": "order.completed",
                "product_id": "no-existe",
                "quantity": "1",
            }
        )

    async def test_ignores_order_created(self, fake_redis):
        fake_redis._store["product:thing"] = {
            "name": "thing",
            "price": 1.0,
            "quantity": 5,
        }
        await _process_order_event(
            {
                "event": "order.created",
                "product_id": "thing",
                "quantity": "3",
            }
        )
        assert fake_redis._store["product:thing"]["quantity"] == 5

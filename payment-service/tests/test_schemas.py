import pytest
from fastapi import HTTPException

from app.schemas import Order, StatusOrder


class TestOrderSave:
    async def test_save_creates_order(self, fake_redis):
        order = Order(
            product_id="test-1",
            price=100.0,
            fee=15.0,
            total=115.0,
            quantity=2,
            status=StatusOrder.PENDING,
        )
        result = await order.save()

        assert result == {
            "product_id": "test-1",
            "price": 100.0,
            "fee": 15.0,
            "total": 115.0,
            "quantity": 2,
            "status": "PENDING",
        }
        assert await fake_redis.exists("order:test-1")

    async def test_save_raises_409_on_duplicate(self):
        await Order(
            product_id="dup",
            price=1.0,
            fee=0.1,
            total=1.1,
            quantity=1,
            status=StatusOrder.PENDING,
        ).save()

        with pytest.raises(HTTPException) as exc:
            await Order(
                product_id="dup",
                price=2.0,
                fee=0.2,
                total=2.2,
                quantity=2,
                status=StatusOrder.COMPLETE,
            ).save()

        assert exc.value.status_code == 409
        assert "dup" in exc.value.detail


class TestOrderGet:
    async def test_get_existing_order(self):
        await Order(
            product_id="get-test",
            price=99.9,
            fee=9.99,
            total=109.89,
            quantity=5,
            status=StatusOrder.PENDING,
        ).save()

        order = await Order.get("get-test")
        assert order is not None
        assert order.product_id == "get-test"
        assert order.price == 99.9
        assert order.fee == 9.99
        assert order.total == 109.89
        assert order.quantity == 5
        assert order.status == StatusOrder.PENDING

    async def test_get_nonexistent_returns_none(self):
        assert await Order.get("no-existe") is None


class TestOrderAllPks:
    async def test_all_pks_empty(self):
        assert await Order.all_pks() == []

    async def test_all_pks_returns_sorted_ids(self):
        await Order(
            product_id="z-last",
            price=1.0,
            fee=0.1,
            total=1.1,
            quantity=1,
            status=StatusOrder.PENDING,
        ).save()
        await Order(
            product_id="a-first",
            price=1.0,
            fee=0.1,
            total=1.1,
            quantity=1,
            status=StatusOrder.COMPLETE,
        ).save()
        await Order(
            product_id="m-mid",
            price=1.0,
            fee=0.1,
            total=1.1,
            quantity=1,
            status=StatusOrder.REFUNDED,
        ).save()

        assert await Order.all_pks() == ["a-first", "m-mid", "z-last"]


class TestOrderUpdateStatus:
    async def test_update_status_existing(self):
        await Order(
            product_id="upd",
            price=100.0,
            fee=15.0,
            total=115.0,
            quantity=2,
            status=StatusOrder.PENDING,
        ).save()

        result = await Order.update_status("upd", StatusOrder.COMPLETE)

        assert result["status"] == "COMPLETE"

        updated = await Order.get("upd")
        assert updated.status == StatusOrder.COMPLETE
        assert updated.price == 100.0

    async def test_update_status_nonexistent_raises_404(self):
        with pytest.raises(HTTPException) as exc:
            await Order.update_status("no-such", StatusOrder.COMPLETE)

        assert exc.value.status_code == 404


class TestOrderDelete:
    async def test_delete_existing_order(self):
        await Order(
            product_id="del-me",
            price=50.0,
            fee=5.0,
            total=55.0,
            quantity=1,
            status=StatusOrder.PENDING,
        ).save()

        result = await Order.delete("del-me")

        assert result == {"message": "Order for product 'del-me' deleted"}
        assert await Order.get("del-me") is None

    async def test_delete_nonexistent_raises_404(self):
        with pytest.raises(HTTPException) as exc:
            await Order.delete("no-such")

        assert exc.value.status_code == 404

import pytest
from fastapi import HTTPException

from app.schemas import Product


class TestProductSave:
    async def test_save_creates_product(self, fake_redis):
        product = Product(name="test-1", price=10.5, quantity=3)
        result = await product.save()

        assert result == {"name": "test-1", "price": 10.5, "quantity": 3}
        assert await fake_redis.exists("product:test-1")

    async def test_save_raises_409_on_duplicate(self):
        await Product(name="dup", price=1.0, quantity=1).save()

        with pytest.raises(HTTPException) as exc:
            await Product(name="dup", price=2.0, quantity=2).save()

        assert exc.value.status_code == 409
        assert "dup" in exc.value.detail


class TestProductGet:
    async def test_get_existing_product(self):
        await Product(name="get-test", price=99.9, quantity=5).save()

        product = await Product.get("get-test")
        assert product is not None
        assert product.name == "get-test"
        assert product.price == 99.9
        assert product.quantity == 5

    async def test_get_nonexistent_returns_none(self):
        assert await Product.get("no-existe") is None


class TestProductAllPks:
    async def test_all_pks_empty(self):
        assert await Product.all_pks() == []

    async def test_all_pks_returns_sorted_names(self):
        await Product(name="z-last", price=1.0, quantity=1).save()
        await Product(name="a-first", price=1.0, quantity=1).save()
        await Product(name="m-mid", price=1.0, quantity=1).save()

        assert await Product.all_pks() == ["a-first", "m-mid", "z-last"]


class TestProductUpdate:
    async def test_update_existing_product(self):
        await Product(name="upd", price=10.0, quantity=1).save()
        result = await Product.update("upd", price=99.9, quantity=5)

        assert result == {"name": "upd", "price": 99.9, "quantity": 5}

        updated = await Product.get("upd")
        assert updated.price == 99.9
        assert updated.quantity == 5

    async def test_update_nonexistent_raises_404(self):
        with pytest.raises(HTTPException) as exc:
            await Product.update("no-such", price=1.0, quantity=1)

        assert exc.value.status_code == 404


class TestProductDelete:
    async def test_delete_existing_product(self):
        await Product(name="del-me", price=5.0, quantity=1).save()
        result = await Product.delete("del-me")

        assert result == {"message": "Product 'del-me' deleted"}
        assert await Product.get("del-me") is None

    async def test_delete_nonexistent_raises_404(self):
        with pytest.raises(HTTPException) as exc:
            await Product.delete("no-such")

        assert exc.value.status_code == 404

"""
Product schema with Redis-backed CRUD operations.

Defines the Product model and provides static methods for persisting,
retrieving, updating, and deleting products in Redis Cloud using the
RedisJSON module.
"""

from __future__ import annotations

from fastapi import HTTPException
from pydantic import BaseModel

from app.redis_client import redis_client


class Product(BaseModel):
    """
    Represents a product with name, price, and quantity.

    :ivar name: The unique product identifier.
    :ivar price: The unit price of the product.
    :ivar quantity: The available stock quantity.
    """

    name: str = ""
    price: float = 0.0
    quantity: int = 0

    def _key(self) -> str:
        """
        Build the Redis key for this product.

        :return: A Redis key in the format ``product:{name}``.
        :rtype: str
        """
        return f"product:{self.name}"

    async def save(self) -> dict:
        """
        Persist the product to Redis.

        :return: The saved product as a dictionary.
        :rtype: dict
        :raises HTTPException 409: If a product with the same name already exists.
        """
        if await redis_client.exists(self._key()):
            raise HTTPException(
                status_code=409, detail=f"Product '{self.name}' already exists"
            )
        await redis_client.json().set(self._key(), "$", self.model_dump())
        return self.model_dump()

    @staticmethod
    async def all_pks() -> list[str]:
        """
        Return a sorted list of all product keys (names).

        :return: A sorted list of product names.
        :rtype: list[str]
        """
        keys = await redis_client.keys("product:*")
        return sorted(key.removeprefix("product:") for key in keys)

    @staticmethod
    async def get(name: str) -> Product | None:
        """
        Fetch a product by name.

        :param name: The unique product name.
        :type name: str
        :return: The Product instance if found, or None.
        :rtype: Product | None
        """
        data = await redis_client.json().get(f"product:{name}")
        if data is None:
            return None
        return Product(**data)

    @staticmethod
    async def update(name: str, price: float, quantity: int) -> dict:
        """
        Update price and quantity of an existing product.

        :param name: The unique product name.
        :type name: str
        :param price: The new unit price.
        :type price: float
        :param quantity: The new stock quantity.
        :type quantity: int
        :return: The updated product as a dictionary.
        :rtype: dict
        :raises HTTPException 404: If the product is not found.
        """
        key = f"product:{name}"
        if not await redis_client.exists(key):
            raise HTTPException(status_code=404, detail=f"Product '{name}' not found")
        updated = Product(name=name, price=price, quantity=quantity)
        await redis_client.json().set(key, "$", updated.model_dump())
        return updated.model_dump()

    @staticmethod
    async def delete(name: str) -> dict:
        """
        Delete a product by name.

        :param name: The unique product name.
        :type name: str
        :return: A confirmation message.
        :rtype: dict
        :raises HTTPException 404: If the product is not found.
        """
        key = f"product:{name}"
        if not await redis_client.exists(key):
            raise HTTPException(status_code=404, detail=f"Product '{name}' not found")
        await redis_client.delete(key)
        return {"message": f"Product '{name}' deleted"}


class UpdateProduct(BaseModel):
    """
    Request body for updating product price and quantity.

    :ivar price: The new unit price.
    :ivar quantity: The new stock quantity.
    """

    price: float
    quantity: int

"""
Order schema with Redis-backed CRUD operations.

Defines the Order model, status enum, and provides static methods for
persisting, retrieving, updating, and deleting orders in Redis Cloud
using the RedisJSON module.
"""

from __future__ import annotations

from enum import Enum

from fastapi import HTTPException
from pydantic import BaseModel

from app.redis_client import redis_client


class StatusOrder(Enum):
    """
    Possible states for an order.

    :ivar PENDING: The order has been created but not yet completed.
    :ivar COMPLETE: The order has been successfully processed.
    :ivar REFUNDED: The order has been refunded.
    """

    PENDING = "PENDING"
    COMPLETE = "COMPLETE"
    REFUNDED = "REFUNDED"


class Order(BaseModel):
    """
    Represents an order with product, pricing, and status.

    :ivar product_id: The unique identifier of the associated product.
    :ivar price: The unit price of the product.
    :ivar fee: The service fee applied to the order.
    :ivar total: The total amount (price + fee) multiplied by quantity.
    :ivar quantity: The number of units ordered.
    :ivar status: The current status of the order.
    """

    product_id: str
    price: float
    fee: float
    total: float
    quantity: int
    status: StatusOrder

    def _key(self) -> str:
        """
        Build the Redis key for this order.

        :return: A Redis key in the format ``order:{product_id}``.
        :rtype: str
        """
        return f"order:{self.product_id}"

    async def save(self) -> dict:
        """
        Persist the order to Redis.

        :return: The saved order as a dictionary.
        :rtype: dict
        :raises HTTPException 409: If an order for the same product already exists.
        """
        if await redis_client.exists(self._key()):
            raise HTTPException(
                status_code=409,
                detail=f"Order for product '{self.product_id}' already exists",
            )
        await redis_client.json().set(self._key(), "$", self.model_dump(mode="json"))
        return self.model_dump(mode="json")

    @staticmethod
    async def all_pks() -> list[str]:
        """
        Return a sorted list of all order keys (product IDs).

        :return: A sorted list of product IDs that have orders.
        :rtype: list[str]
        """
        keys = await redis_client.keys("order:*")
        return sorted(key.removeprefix("order:") for key in keys)

    @staticmethod
    async def get(product_id: str) -> Order | None:
        """
        Fetch an order by product_id.

        :param product_id: The unique product identifier.
        :type product_id: str
        :return: The Order instance if found, or None.
        :rtype: Order | None
        """
        data = await redis_client.json().get(f"order:{product_id}")
        if data is None:
            return None
        return Order(**data)

    @staticmethod
    async def update_status(product_id: str, status: StatusOrder) -> dict:
        """
        Updates the status of an order for a given product.

        This method retrieves an order based on the product ID and updates its
        status. If the order does not exist in the database, an exception is
        raised. A JSON representation of the updated order is returned.

        :param product_id: The unique identifier of the product associated with
            the order.
        :type product_id: str
        :param status: The new status to assign to the order.
        :type status: StatusOrder
        :return: A dictionary representation of the updated order.
        :rtype: dict
        :raises HTTPException: If the order for the given product ID is not
            found.
        """
        key = f"order:{product_id}"
        if not await redis_client.exists(key):
            raise HTTPException(
                status_code=404,
                detail=f"Order for product '{product_id}' not found",
            )
        existing = Order(**await redis_client.json().get(key))
        existing.status = status
        await redis_client.json().set(key, "$", existing.model_dump(mode="json"))
        return existing.model_dump(mode="json")

    @staticmethod
    async def delete(product_id: str) -> dict:
        """
        Delete an order by product_id.

        :param product_id: The unique product identifier.
        :type product_id: str
        :return: A confirmation message.
        :rtype: dict
        :raises HTTPException 404: If the order is not found.
        """
        key = f"order:{product_id}"
        if not await redis_client.exists(key):
            raise HTTPException(
                status_code=404,
                detail=f"Order for product '{product_id}' not found",
            )
        await redis_client.delete(key)
        return {"message": f"Order for product '{product_id}' deleted"}


class UpdateOrderStatus(BaseModel):
    """
    Request body for updating an order's status.

    :ivar status: The new status to assign to the order.
    """

    status: StatusOrder

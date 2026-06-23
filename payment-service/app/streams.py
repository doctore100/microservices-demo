"""
Stream event publishers for order events.

Provides helpers to publish order-related events to Redis Streams
so that other services (e.g., inventory) can react asynchronously.
"""

from app.redis_client import redis_client
from app.schemas import Order

STREAM = "order:events"


async def publish_order_created(order: Order) -> None:
    """
    Publish an order.created event to the order:events stream.

    :param order: The newly created order.
    :type order: Order
    """
    await redis_client.xadd(
        STREAM,
        {
            "event": "order.created",
            "product_id": order.product_id,
            "quantity": str(order.quantity),
            "total": str(order.total),
        },
        maxlen=1000,
    )


async def publish_order_completed(product_id: str, quantity: int) -> None:
    """
    Publish an order.completed event.

    :param product_id: The product associated with the completed order.
    :type product_id: str
    :param quantity: The quantity ordered.
    :type quantity: int
    """
    await redis_client.xadd(
        STREAM,
        {
            "event": "order.completed",
            "product_id": product_id,
            "quantity": str(quantity),
        },
        maxlen=1000,
    )


async def publish_order_refunded(product_id: str, quantity: int) -> None:
    """
    Publish an order.refunded event.

    :param product_id: The product associated with the refunded order.
    :type product_id: str
    :param quantity: The quantity refunded.
    :type quantity: int
    """
    await redis_client.xadd(
        STREAM,
        {
            "event": "order.refunded",
            "product_id": product_id,
            "quantity": str(quantity),
        },
        maxlen=1000,
    )


async def publish_order_deleted(product_id: str) -> None:
    """
    Publish an order.deleted event to the order:events stream.

    :param product_id: The product associated with the deleted order.
    :type product_id: str
    """
    await redis_client.xadd(
        STREAM,
        {
            "event": "order.deleted",
            "product_id": product_id,
        },
        maxlen=1000,
    )

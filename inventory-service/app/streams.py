"""
Stream event publishers for inventory events.

Provides helpers to publish product-related events to Redis Streams
so that other services (e.g., payment) can react asynchronously.
"""

from app.redis_client import redis_client
from app.schemas import Product

STREAM = "product:events"


async def publish_product_created(product: Product) -> None:
    """
    Publish a product.created event to the product:events stream.

    :param product: The newly created product.
    :type product: Product
    """
    await redis_client.xadd(
        STREAM,
        {
            "event": "product.created",
            "name": product.name,
            "price": str(product.price),
            "quantity": str(product.quantity),
        },
        maxlen=1000,
    )


async def publish_product_deleted(name: str) -> None:
    """
    Publish a product.deleted event to the product:events stream.

    :param name: The name of the deleted product.
    :type name: str
    """
    await redis_client.xadd(
        STREAM,
        {
            "event": "product.deleted",
            "name": name,
        },
        maxlen=1000,
    )

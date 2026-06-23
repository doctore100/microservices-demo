"""
Background consumer of product:events stream.

Listens for product.created and product.deleted events to maintain the
products:valid set and automatically refund PENDING orders when a
product is deleted.
"""

import asyncio

from redis import ResponseError

from app.redis_client import redis_client
from app.schemas import Order, StatusOrder

STREAM = "product:events"
GROUP = "payment-group"
CONSUMER = "payment-consumer-1"


async def consume_products() -> None:
    """
    Continuously read the product:events stream via a consumer group.

    Each message is processed and acknowledged. Designed to run as a
    background asyncio task inside the FastAPI lifespan.
    """
    try:
        await redis_client.xgroup_create(STREAM, GROUP, id="$", mkstream=True)
    except ResponseError:
        pass

    while True:
        try:
            messages = await redis_client.xreadgroup(
                GROUP, CONSUMER, {STREAM: ">"}, count=10, block=5000
            )
            if not messages:
                continue
            for _stream_name, entries in messages:
                for msg_id, data in entries:
                    await _process_product_event(data)
                    await redis_client.xack(STREAM, GROUP, msg_id)
        except asyncio.CancelledError:
            break
        except Exception:
            await asyncio.sleep(1)


async def _process_product_event(data: dict) -> None:
    """
    Update the products:valid cache and handle deletion side-effects.

    :param data: The stream message payload.
    :type data: dict
    """
    event = data.get("event")
    name = data.get("name")

    if event == "product.created" and name:
        await redis_client.sadd("products:valid", name)
    elif event == "product.deleted" and name:
        await redis_client.srem("products:valid", name)
        key = f"order:{name}"
        order_data = await redis_client.json().get(key)
        if order_data and order_data.get("status") == "PENDING":
            order = Order(**order_data)
            order.status = StatusOrder.REFUNDED
            await redis_client.json().set(key, "$", order.model_dump(mode="json"))

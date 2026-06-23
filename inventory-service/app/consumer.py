"""
Background consumer of order:events stream.

Listens for order.completed and order.refunded events and adjusts
the corresponding product stock in Redis.
"""

import asyncio

from redis import ResponseError

from app.redis_client import redis_client

STREAM = "order:events"
GROUP = "inventory-group"
CONSUMER = "inventory-consumer-1"


async def consume_orders() -> None:
    """
    Continuously read the order:events stream via a consumer group.

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
                    await _process_order_event(data)
                    await redis_client.xack(STREAM, GROUP, msg_id)
        except asyncio.CancelledError:
            break
        except Exception:
            await asyncio.sleep(1)


async def _process_order_event(data: dict) -> None:
    """
    Adjust product stock based on the order event.

    :param data: The stream message payload.
    :type data: dict
    """
    event = data.get("event")
    product_id = data.get("product_id")
    quantity = int(data.get("quantity", 0))

    if event not in ("order.completed", "order.refunded") or not product_id:
        return

    key = f"product:{product_id}"
    product_data = await redis_client.json().get(key)
    if product_data is None:
        return

    if event == "order.completed":
        product_data["quantity"] -= quantity
    else:
        product_data["quantity"] += quantity

    await redis_client.json().set(key, "$", product_data)

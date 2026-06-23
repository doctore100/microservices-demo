"""
Payment service — FastAPI application for order management.

Provides REST endpoints to create, read, update, and delete orders.
Orders are stored in Redis Cloud using the RedisJSON module.
"""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from app.consumer import consume_products
from app.redis_client import redis_client
from app.schemas import Order, StatusOrder, UpdateOrderStatus
from app.streams import (
    publish_order_completed,
    publish_order_created,
    publish_order_deleted,
    publish_order_refunded,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage the Redis client lifecycle and background consumer.

    :param app: The FastAPI application instance.
    :type app: FastAPI
    """
    task = asyncio.create_task(consume_products())
    yield
    task.cancel()
    await task
    await redis_client.aclose()


app = FastAPI(lifespan=lifespan)


async def _product_exists(product_id: str) -> bool:
    """
    Check whether a product exists in the inventory.

    Uses the products:valid set (eventually consistent cache) first,
    then falls back to a direct EXISTS check on the product key.

    :param product_id: The product identifier to look up.
    :type product_id: str
    :return: True if the product exists, False otherwise.
    :rtype: bool
    """
    if await redis_client.sismember("products:valid", product_id):
        return True
    return await redis_client.exists(f"product:{product_id}")


@app.get("/")
async def root():
    """
    Health check endpoint.

    :return: A simple greeting message.
    :rtype: dict
    """
    return {"message": "Hello World --> 2"}


@app.get("/orders")
async def get_all_orders():
    """
    List all order keys (product IDs).

    :return: A sorted list of product IDs that have orders.
    :rtype: list[str]
    """
    return await Order.all_pks()


@app.post("/orders")
async def create_order(order: Order):
    """
    Create a new order.

    Validates that the referenced product exists in the inventory
    before persisting the order.

    :param order: The order data to persist.
    :type order: Order
    :return: The created order as a dictionary.
    :rtype: dict
    :raises HTTPException 400: If the referenced product does not exist.
    :raises HTTPException 409: If an order for the same product already exists.
    """
    if not await _product_exists(order.product_id):
        raise HTTPException(
            status_code=400,
            detail=f"Product '{order.product_id}' not found in inventory",
        )
    result = await order.save()
    await publish_order_created(order)
    return result


@app.get("/orders/{product_id}")
async def get_order(product_id: str):
    """
    Get an order by product_id.

    :param product_id: The unique product identifier.
    :type product_id: str
    :return: The order data if found.
    :rtype: Order
    :raises HTTPException 404: If the order is not found.
    """
    order = await Order.get(product_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@app.put("/orders/{product_id}")
async def update_order_status(product_id: str, body: UpdateOrderStatus):
    """
    Update the status of an existing order.

    Publishes completion or refund events so the inventory service
    can adjust stock accordingly.

    :param product_id: The unique product identifier.
    :type product_id: str
    :param body: The new status value.
    :type body: UpdateOrderStatus
    :return: The updated order as a dictionary.
    :rtype: dict
    :raises HTTPException 404: If the order is not found.
    """
    result = await Order.update_status(product_id, body.status)
    if body.status == StatusOrder.COMPLETE:
        await publish_order_completed(product_id, result["quantity"])
    elif body.status == StatusOrder.REFUNDED:
        await publish_order_refunded(product_id, result["quantity"])
    return result


@app.delete("/orders/{product_id}")
async def delete_order(product_id: str):
    """
    Delete an order by product_id.

    :param product_id: The unique product identifier.
    :type product_id: str
    :return: A confirmation message.
    :rtype: dict
    :raises HTTPException 404: If the order is not found.
    """
    result = await Order.delete(product_id)
    await publish_order_deleted(product_id)
    return result

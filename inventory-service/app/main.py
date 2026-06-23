"""
Inventory service — FastAPI application for product CRUD.

Provides REST endpoints to create, read, update, and delete products.
Products are stored in Redis Cloud using the RedisJSON module.
"""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from app.consumer import consume_orders
from app.redis_client import redis_client
from app.schemas import Product, UpdateProduct
from app.streams import publish_product_created, publish_product_deleted


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage the Redis client lifecycle and background consumer.

    :param app: The FastAPI application instance.
    :type app: FastAPI
    """
    task = asyncio.create_task(consume_orders())
    yield
    task.cancel()
    await task
    await redis_client.aclose()


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root():
    """
    Health check endpoint.

    :return: A simple greeting message.
    :rtype: dict
    """
    return {"message": "Hello World --> 1"}


@app.get("/products")
async def get_all_products():
    """
    List all product names.

    :return: A sorted list of product names stored in Redis.
    :rtype: list[str]
    """
    return await Product.all_pks()


@app.post("/products")
async def create_product(product: Product):
    """
    Create a new product.

    :param product: The product data to persist.
    :type product: Product
    :return: The created product as a dictionary.
    :rtype: dict
    :raises HTTPException 409: If a product with the same name already exists.
    """
    result = await product.save()
    await publish_product_created(product)
    return result


@app.get("/products/{name}")
async def get_product(name: str):
    """
    Get a product by name.

    :param name: The unique product name.
    :type name: str
    :return: The product data if found.
    :rtype: Product
    :raises HTTPException 404: If the product is not found.
    """
    product = await Product.get(name)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.put("/products/{name}")
async def update_product(name: str, body: UpdateProduct):
    """
    Update an existing product's price and quantity.

    :param name: The unique product name to update.
    :type name: str
    :param body: The updated price and quantity values.
    :type body: UpdateProduct
    :return: The updated product as a dictionary.
    :rtype: dict
    :raises HTTPException 404: If the product is not found.
    """
    return await Product.update(name, body.price, body.quantity)


@app.delete("/products/{name}")
async def delete_product(name: str):
    """
    Delete a product by name.

    :param name: The unique product name to delete.
    :type name: str
    :return: A confirmation message.
    :rtype: dict
    :raises HTTPException 404: If the product is not found.
    """
    result = await Product.delete(name)
    await publish_product_deleted(name)
    return result

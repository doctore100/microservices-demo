# API Reference

## Health Check

```
GET /
```

**Response** `200 OK`
```json
{
  "message": "Hello World --> 2"
}
```

---

## Listar órdenes

```
GET /orders
```

**Response** `200 OK`
```json
[
  "producto-1",
  "producto-2"
]
```

---

## Crear orden

```
POST /orders
Content-Type: application/json
```

**Request body**
```json
{
  "product_id": "producto-1",
  "price": 123.6,
  "fee": 10.0,
  "total": 133.6,
  "quantity": 1,
  "status": "PENDING"
}
```

**Response** `200 OK` — orden creada
```json
{
  "product_id": "producto-1",
  "price": 123.6,
  "fee": 10.0,
  "total": 133.6,
  "quantity": 1,
  "status": "PENDING"
}
```

**Response** `400 Bad Request` — producto no encontrado en inventario
```json
{
  "detail": "Product 'producto-1' not found in inventory"
}
```

**Response** `409 Conflict` — orden duplicada para el mismo producto
```json
{
  "detail": "Order for product 'producto-1' already exists"
}
```

---

## Obtener orden

```
GET /orders/{product_id}
```

**Response** `200 OK`
```json
{
  "product_id": "producto-1",
  "price": 123.6,
  "fee": 10.0,
  "total": 133.6,
  "quantity": 1,
  "status": "PENDING"
}
```

**Response** `404 Not Found`
```json
{
  "detail": "Order not found"
}
```

---

## Actualizar estado de orden

```
PUT /orders/{product_id}
Content-Type: application/json
```

**Request body**
```json
{
  "status": "COMPLETE"
}
```

**Response** `200 OK` — orden actualizada
```json
{
  "product_id": "producto-1",
  "price": 123.6,
  "fee": 10.0,
  "total": 133.6,
  "quantity": 1,
  "status": "COMPLETE"
}
```

Estados disponibles: `PENDING`, `COMPLETE`, `REFUNDED`.

Al actualizar a `COMPLETE` se publica un evento `order.completed` que descuenta stock en el inventario.
Al actualizar a `REFUNDED` se publica un evento `order.refunded` que reaumenta stock en el inventario.

**Response** `404 Not Found`
```json
{
  "detail": "Order for product 'producto-1' not found"
}
```

---

## Eliminar orden

```
DELETE /orders/{product_id}
```

**Response** `200 OK` — orden eliminada
```json
{
  "message": "Order for product 'producto-1' deleted"
}
```

**Response** `404 Not Found`
```json
{
  "detail": "Order for product 'producto-1' not found"
}
```

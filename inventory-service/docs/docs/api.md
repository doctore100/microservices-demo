# API Reference

## Health Check

```
GET /
```

**Response** `200 OK`
```json
{
  "message": "Hello World--> 1"
}
```

---

## Listar productos

```
GET /products
```

**Response** `200 OK`
```json
[
  "producto-1",
  "producto-2"
]
```

---

## Crear producto

```
POST /products
Content-Type: application/json
```

**Request body**
```json
{
  "name": "producto-1",
  "price": 123.6,
  "quantity": 23
}
```

**Response** `200 OK` — producto creado
```json
{
  "name": "producto-1",
  "price": 123.6,
  "quantity": 23
}
```

**Response** `409 Conflict` — producto duplicado
```json
{
  "detail": "Product 'producto-1' already exists"
}
```

---

## Obtener producto

```
GET /products/{name}
```

**Response** `200 OK`
```json
{
  "name": "producto-1",
  "price": 123.6,
  "quantity": 23
}
```

**Response** `404 Not Found`
```json
{
  "detail": "Product not found"
}
```

---

## Actualizar producto

```
PUT /products/{name}
Content-Type: application/json
```

**Request body**
```json
{
  "price": 99.9,
  "quantity": 5
}
```

**Response** `200 OK` — producto actualizado
```json
{
  "name": "producto-1",
  "price": 99.9,
  "quantity": 5
}
```

**Response** `404 Not Found`
```json
{
  "detail": "Product 'producto-1' not found"
}
```

---

## Eliminar producto

```
DELETE /products/{name}
```

**Response** `200 OK` — producto eliminado
```json
{
  "message": "Product 'producto-1' deleted"
}
```

**Response** `404 Not Found`
```json
{
  "detail": "Product 'producto-1' not found"
}
```

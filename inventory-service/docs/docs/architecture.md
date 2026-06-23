# Arquitectura

## Visión general

El sistema sigue una arquitectura de **microservicios** donde cada servicio es independiente y se comunica de forma asíncrona a través de **Redis Streams**.

```
┌──────────────────────────┐       product:events       ┌──────────────────────────┐
│     Inventory Service    │ ───────────────────────────►│      Payment Service     │
│  (FastAPI + RedisJSON)   │◄───────────────────────────│   (FastAPI + RedisJSON)  │
│  Productos CRUD          │       order:events         │   Órdenes CRUD           │
│  Stock adjustment        │                            │   Cache + auto-refund    │
└────────────┬─────────────┘                            └─────────────┬────────────┘
             │                                                       │
             └────────────────────────┬──────────────────────────────┘
                                      │
                           ┌──────────▼──────────┐
                           │     Redis Cloud      │
                           │  (RedisJSON +        │
                           │   Streams + Sets)    │
                           └─────────────────────┘
```

Ambos servicios comparten la misma instancia de Redis Cloud. Cada uno expone una API REST independiente (FastAPI) y ejecuta un consumidor de eventos en segundo plano dentro del lifespan de la aplicación.

## Inventory Service

### Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/` | Health check |
| GET | `/products` | Lista todos los productos |
| POST | `/products` | Crea un producto |
| GET | `/products/{name}` | Obtiene un producto por nombre |
| PUT | `/products/{name}` | Actualiza precio y cantidad |
| DELETE | `/products/{name}` | Elimina un producto |

### Almacenamiento

Los productos se guardan en Redis usando el módulo **RedisJSON** con la estructura:

```
Key:    product:{name}
Value:  {"name": "...", "price": ..., "quantity": ...}
```

El formato JSON preserva los tipos de datos (string, float, int).

### Eventos publicados

| Stream | Evento | Cuándo |
|---|---|---|
| `product:events` | `product.created` | Después de crear un producto (POST) |
| `product:events` | `product.deleted` | Después de eliminar un producto (DELETE) |

### Consumidor de eventos

El servicio ejecuta `consume_orders()` como tarea de fondo en el lifespan. Lee del stream `order:events` usando un consumer group (`inventory-group`) y ajusta el stock según el evento:

- `order.completed` → descuenta la cantidad del stock del producto
- `order.refunded` → reaumenta la cantidad al stock del producto

Los eventos `order.created` y `order.deleted` se ignoran (no afectan al inventario).

## Payment Service

### Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/` | Health check |
| GET | `/orders` | Lista todas las órdenes |
| POST | `/orders` | Crea una orden |
| GET | `/orders/{product_id}` | Obtiene una orden por ID de producto |
| PUT | `/orders/{product_id}` | Actualiza el estado de una orden |
| DELETE | `/orders/{product_id}` | Elimina una orden |

### Almacenamiento

Las órdenes se guardan en Redis usando el módulo **RedisJSON** con la estructura:

```
Key:    order:{product_id}
Value:  {"product_id": "...", "price": ..., "fee": ..., "total": ..., "quantity": ..., "status": "PENDING|COMPLETE|REFUNDED"}
```

### Validación de productos

Antes de crear una orden, el servicio verifica que el producto exista en el inventario mediante una estrategia híbrida:

1. Consulta el conjunto `products:valid` (Set Redis) — cache O(1)
2. Si no está en el cache, hace fallback a `EXISTS product:{product_id}`

### Eventos publicados

| Stream | Evento | Cuándo |
|---|---|---|
| `order:events` | `order.created` | Después de crear una orden (POST) |
| `order:events` | `order.completed` | Al cambiar estado a COMPLETE (PUT) |
| `order:events` | `order.refunded` | Al cambiar estado a REFUNDED (PUT) |
| `order:events` | `order.deleted` | Después de eliminar una orden (DELETE) |

### Consumidor de eventos

El servicio ejecuta `consume_products()` como tarea de fondo en el lifespan. Lee del stream `product:events` usando un consumer group (`payment-group`) y mantiene el cache de productos válidos:

- `product.created` → agrega el nombre al conjunto `products:valid`
- `product.deleted` → elimina el nombre de `products:valid` y auto-refundea cualquier orden PENDING asociada a ese producto

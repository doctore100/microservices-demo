# Arquitectura

## Visión general

El sistema sigue una arquitectura de **microservicios** donde cada servicio es independiente y se comunica a través de Redis.

```
┌─────────────────────┐     ┌─────────────────────┐
│  Inventory Service  │     │   Payment Service   │
│  (FastAPI + Redis)  │     │  (FastAPI + Redis)  │
└─────────┬───────────┘     └──────────┬──────────┘
          │                            │
          └──────────┬─────────────────┘
                     │
          ┌──────────▼──────────┐
          │   Redis Cloud       │
          │   (base de datos    │
          │    compartida)      │
          └─────────────────────┘
```

## Inventory Service

### Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/` | Health check |
| GET | `/products` | Lista todos los productos |
| POST | `/products` | Crea un producto |
| GET | `/products/{name}` | Obtiene un producto por nombre |

### Almacenamiento

Los productos se guardan en Redis usando el módulo **RedisJSON** con la estructura:

```
Key:    product:{name}
Value:  {"name": "...", "price": ..., "quantity": ...}
```

El formato JSON preserva los tipos de datos (string, float, int).

## Payment Service

Actualmente en fase inicial con endpoints básicos (`GET /`, `GET /hello/{name}`).

## Comunicación entre servicios

Pendiente de implementar (Redis Pub/Sub o similar en `consumer.py`).

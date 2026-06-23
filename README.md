# Microservices Demo

[![Python](https://img.shields.io/badge/Python-3.14+-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.137-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Redis](https://img.shields.io/badge/Redis_Cloud-red?logo=redis)](https://redis.com)
[![tests: 57 passing](https://img.shields.io/badge/tests-57%20passing-brightgreen)](https://github.com/doctore100/microservices-demo)
[![code style: ruff](https://img.shields.io/badge/code%20style-ruff-261230)](https://docs.astral.sh/ruff)
[![docs: mkdocs](https://img.shields.io/badge/docs-mkdocs%20material-2ea44f?logo=materialformkdocs)](https://www.mkdocs.org)
[![license: MIT](https://img.shields.io/badge/license-MIT-yellow)](LICENSE)

## Descripción

Sistema educacional de microservicios con **FastAPI** + **Redis Cloud**, donde dos servicios independientes se comunican de forma asíncrona mediante **Redis Streams**.

- **Inventory Service** — CRUD de productos, ajuste de stock vía eventos
- **Payment Service** — CRUD de órdenes, validación de existencia de producto, auto-refund

## Arquitectura

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

Cada servicio corre como un proceso FastAPI independiente, comparte la misma instancia de Redis Cloud y se comunica exclusivamente a través de **Redis Streams** con consumer groups.

## Servicios

### Inventory Service (`inventory-service/`)

| Endpoint | Método | Descripción |
|---|---|---|
| `/` | GET | Health check |
| `/products` | GET | Listar productos |
| `/products` | POST | Crear producto |
| `/products/{name}` | GET | Obtener producto |
| `/products/{name}` | PUT | Actualizar producto |
| `/products/{name}` | DELETE | Eliminar producto |

- Persiste productos en RedisJSON bajo la clave `product:{name}`
- Publica eventos `product.created` y `product.deleted` al stream `product:events`
- Consume el stream `order:events` — descuenta stock en `order.completed`, reaumenta en `order.refunded`

### Payment Service (`payment-service/`)

| Endpoint | Método | Descripción |
|---|---|---|
| `/` | GET | Health check |
| `/orders` | GET | Listar órdenes |
| `/orders` | POST | Crear orden |
| `/orders/{product_id}` | GET | Obtener orden |
| `/orders/{product_id}` | PUT | Actualizar estado |
| `/orders/{product_id}` | DELETE | Eliminar orden |

- Persiste órdenes en RedisJSON bajo la clave `order:{product_id}`
- Valida existencia del producto: primero consulta el cache `products:valid` (set Redis), luego fallback a `EXISTS` directo
- Publica eventos `order.created`, `order.completed`, `order.refunded` y `order.deleted` al stream `order:events`
- Consume el stream `product:events` — mantiene el cache `products:valid` y ejecuta auto-refund de órdenes PENDING cuando un producto se elimina

## Comunicación por Eventos

| Stream | Evento | Emisor | Receptor | Efecto |
|---|---|---|---|---|
| `product:events` | `product.created` | Inventory | Payment | `SADD products:valid` |
| `product:events` | `product.deleted` | Inventory | Payment | `SREM` + auto-refund de PENDING |
| `order:events` | `order.completed` | Payment | Inventory | Decrementa stock del producto |
| `order:events` | `order.refunded` | Payment | Inventory | Incrementa stock del producto |
| `order:events` | `order.created` | Payment | — | Solo logging |
| `order:events` | `order.deleted` | Payment | — | Solo logging |

Los consumidores se ejecutan como tareas asíncronas de fondo dentro del lifespan de cada aplicación FastAPI. Cada uno utiliza `XREADGROUP` con `block=5000ms` y realiza `XACK` después de procesar cada mensaje.

## Stack Tecnológico

| Componente | Tecnología |
|---|---|
| Lenguaje | Python 3.14+ |
| Framework web | FastAPI 0.137 |
| Validación | Pydantic v2 |
| Base de datos | Redis Cloud (módulo RedisJSON) |
| Comunicación | Redis Streams (consumer groups) |
| Gestión de dependencias | Poetry |
| Calidad de código | Ruff (lint + format + reglas D, E, F, I, N, UP, W) |
| Tests | pytest + pytest-asyncio + FakeRedis |
| Documentación | MkDocs con tema Material |

## Requisitos

- Python 3.14 o superior
- Poetry (`pip install poetry`)
- Una instancia de [Redis Cloud](https://redis.com/redis-enterprise-cloud/) (plan gratuito suficiente)

## Configuración

### 1. Clonar el repositorio

```bash
git clone https://github.com/doctore100/microservices-demo.git
cd microservices-demo
```

### 2. Configurar credenciales Redis

Cada servicio necesita su propio archivo `.env` con las credenciales de Redis Cloud:

```bash
cp inventory-service/.env.example inventory-service/.env
# editar inventory-service/.env con tus credenciales

cp payment-service/.env.example payment-service/.env
# editar payment-service/.env con tus credenciales
```

**Contenido de `.env.example`:**

```ini
REDIS_HOST=redis-xxxxx.cXXXXX.us-east-x-x.ec2.cloud.redislabs.com
REDIS_PASSWORD=tu_contraseña_segura
REDIS_PORT=10073
```

### 3. Instalar dependencias

```bash
cd inventory-service
poetry install
cd ..

cd payment-service
poetry install
cd ..
```

Cada servicio crea su propio entorno virtual en `.venv/` (configuración `virtualenvs.in-project = true`).

### 4. Ejecutar servicios

En terminales separadas:

```bash
# Terminal 1 — Inventory Service (puerto 8000)
cd inventory-service
poetry run uvicorn app.main:app --reload --port 8000
```

```bash
# Terminal 2 — Payment Service (puerto 8001)
cd payment-service
poetry run uvicorn app.main:app --reload --port 8001
```

Health checks:
- Inventory → http://127.0.0.1:8000 → `{"message": "Hello World --> 1"}`
- Payment → http://127.0.0.1:8001 → `{"message": "Hello World --> 2"}`
- Documentación interactiva Swagger en `/docs` de cada servicio.

## Calidad de Código

```bash
# Linter (cada servicio)
poetry run ruff check .

# Formatter
poetry run ruff format .
```

## Tests

```bash
# Inventory Service — 26 tests
cd inventory-service && poetry run pytest -v

# Payment Service — 31 tests
cd payment-service && poetry run pytest -v

# Total: 57 tests
```

Los tests utilizan `FakeRedis` (simulación en memoria de Redis) y `pytest-asyncio` con `asyncio_mode = auto`. No requieren conexión a Redis real.

## Documentación

Cada servicio incluye su propia documentación generada con MkDocs:

```bash
cd inventory-service
poetry run mkdocs serve   # http://127.0.0.1:4000

cd payment-service
poetry run mkdocs serve   # http://127.0.0.1:4001
```

## Estructura del Proyecto

```
microservices-demo/
├── .gitignore
├── README.md
├── inventory-service/
│   ├── .env.example
│   ├── .env                         # (ignorado por git)
│   ├── pyproject.toml
│   ├── poetry.lock
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                  # FastAPI app, endpoints, lifespan
│   │   ├── schemas.py               # Product model + CRUD async
│   │   ├── streams.py               # Publicadores de eventos
│   │   ├── consumer.py              # Consumidor de order:events
│   │   ├── redis_client.py          # Cliente Redis singleton
│   │   └── config/
│   │       └── settings.py          # Settings desde .env
│   ├── tests/
│   │   ├── conftest.py              # FakeRedis fixtures
│   │   ├── test_main.py
│   │   ├── test_schemas.py
│   │   └── test_streams.py
│   └── docs/
│       ├── mkdocs.yml
│       └── docs/
│           ├── index.md
│           ├── architecture.md
│           └── api.md
├── payment-service/
│   ├── .env.example
│   ├── .env                         # (ignorado por git)
│   ├── pyproject.toml
│   ├── poetry.lock
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                  # FastAPI app, endpoints, lifespan
│   │   ├── schemas.py               # Order model + StatusOrder enum + CRUD async
│   │   ├── streams.py               # Publicadores de eventos
│   │   ├── consumer.py              # Consumidor de product:events
│   │   ├── redis_client.py          # Cliente Redis singleton
│   │   └── config/
│   │       └── settings.py          # Settings desde .env
│   ├── tests/
│   │   ├── conftest.py              # FakeRedis fixtures + seed_products
│   │   ├── test_main.py
│   │   ├── test_schemas.py
│   │   └── test_streams.py
│   └── docs/
│       ├── mkdocs.yml
│       └── docs/
│           ├── index.md
│           └── api.md
```

## Licencia

```
MIT License

Copyright (c) 2026 David Guzman

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

Creado con ❤️ por [David Guzman](https://github.com/doctore100)

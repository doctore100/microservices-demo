# Inventory Service

Microservicio de inventario construido con **FastAPI** y **Redis**.

## Stack

| Componente | Tecnología |
|------------|-----------|
| Framework | FastAPI 0.137 |
| Servidor ASGI | Uvicorn 0.49 |
| Base de datos | Redis 8.0 (Redis Cloud) |
| Validación | Pydantic 2.13 |
| Configuración | Pydantic-Settings |
| Testing | pytest + pytest-mock |
| Documentación | MkDocs Material |

## Estructura del proyecto

```
inventory-service/
├── app/
│   ├── main.py          # Endpoints FastAPI
│   ├── schemas.py       # Modelo Product + CRUD async
│   ├── streams.py       # Publicadores de eventos Redis Streams
│   ├── consumer.py      # Consumidor de order:events
│   ├── redis_client.py  # Cliente Redis singleton
│   └── config/
│       └── settings.py  # Config desde .env
├── tests/
│   ├── conftest.py      # Fixtures y mocks
│   ├── test_schemas.py  # Tests unitarios
│   ├── test_main.py     # Tests de integración
│   └── test_streams.py  # Tests de eventos
├── docs/                # Documentación
├── .env                 # Variables de entorno
└── pyproject.toml       # Dependencias
```

## Puertos

| Servicio | Puerto |
|----------|--------|
| API (FastAPI) | `8000` |
| Documentación (MkDocs) | `4000` |

## Ejecución

```bash
cd inventory-service

# API
uvicorn app.main:app --reload          # http://localhost:8000

# Documentación
mkdocs serve -f docs/mkdocs.yml        # http://localhost:4000
```

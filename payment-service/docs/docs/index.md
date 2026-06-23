# Payment Service

Microservicio de pagos construido con **FastAPI** y **Redis**.

## Stack

| Componente | Tecnología |
|------------|-----------|
| Framework | FastAPI 0.137 |
| Servidor ASGI | Uvicorn 0.49 |
| Base de datos | Redis 8.0 (Redis Cloud) |
| Validación | Pydantic 2.13 |
| Configuración | Pydantic-Settings |

## Estado

Actualmente en desarrollo inicial. Pendiente de implementar lógica de pagos.

## Puertos

| Servicio | Puerto |
|----------|--------|
| API (FastAPI) | `8001` |
| Documentación (MkDocs) | `4001` |

## Ejecución

```bash
cd payment-service

# API
uvicorn app.main:app --reload          # http://localhost:8001

# Documentación
mkdocs serve -f docs/mkdocs.yml        # http://localhost:4001
```

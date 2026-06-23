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

## Saludo

```
GET /hello/{name}
```

**Response** `200 OK`
```json
{
  "message": "Hello {name}"
}
```

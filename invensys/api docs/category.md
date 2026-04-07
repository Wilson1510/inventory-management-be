# API Endpoints and Payload

## List
**Endpoint:** `GET /api/categories/`

**Response:**
```json
[
    {
        "name": "Test Product",
        "id": 6,
        "created_at": "2026-04-04T06:22:34.514325Z",
        "created_by": 9,
        "updated_at": "2026-04-04T06:22:34.514327Z",
        "updated_by": null
    },
    {
        "name": "Test Product 2",
        "id": 7,
        "created_at": "2026-04-04T07:22:34.514325Z",
        "created_by": 10,
        "updated_at": "2026-04-04T07:22:34.514327Z",
        "updated_by": 10
    }
]
```

## Retrieve
**Endpoint:** `GET /api/categories/{id}`
**Response:**
```json
{
    "name": "Test Product",
    "id": 6,
    "created_at": "2026-04-04T06:23:57.253807Z",
    "created_by": 9,
    "updated_at": "2026-04-04T06:23:57.253809Z",
    "updated_by": 9
}
```

## Create
**Endpoint:** `POST /api/categories/`
**Request Body:**
```json
{
    "name": "Test Product"
}
```
**Response:**
```json
{
    "name": "Test Product",
    "id": 6,
    "created_at": "2026-04-04T06:23:57.253807Z",
    "created_by": 9,
    "updated_at": "2026-04-04T06:23:57.253809Z",
    "updated_by": 9
}
```

## Update (PUT and PATCH)
**Endpoint:** `PUT /api/categories/{id}`
**Request Body:**
PUT send all fields
PATCH send only changed fields
```json
{
    "name": "Test Product"
}
```
**Response:**
PUT send all fields
PATCH send only changed fields
```json
{
    "name": "Test Product",
    "id": 6,
    "created_at": "2026-04-04T06:23:57.253807Z",
    "created_by": 9,
    "updated_at": "2026-04-04T06:23:57.253809Z",
    "updated_by": 9
}
```

## Delete
**Endpoint:** `DELETE /api/categories/{id}`
**Response:** `204 No Content`
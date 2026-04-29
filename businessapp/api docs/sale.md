# API Endpoints and Payload

* Sales mirrors Purchase closely, mapped to supplier_id and arrival_date

## List
**Endpoint:** `GET /api/sales/`

**Response:**
```json
[
    {
        "number": "SO-00001",
        "status": "DRAFT",
        "total": "10000000.00",
        "customer": { "id": 1, "name": "ACME Corp" },
        "delivery_date": "2026-05-15",
        "id": 6,
        "created_at": "2026-04-04T06:22:34.514325Z",
        "created_by": 9,
        "updated_at": "2026-04-04T06:22:34.514327Z",
        "updated_by": null
    },
    {
        "number": "SO-00002",
        "status": "CONFIRMED",
        "total": "10000000.00",
        "customer": { "id": 1, "name": "ACME Corp" },
        "delivery_date": "2026-05-15",
        "id": 7,
        "created_at": "2026-04-04T07:22:34.514325Z",
        "created_by": 10,
        "updated_at": "2026-04-04T07:22:34.514327Z",
        "updated_by": 10
    }
]
```

## Retrieve
**Endpoint:** `GET /api/sales/{id}`
**Response:**
```json
{
    "number": "SO-00001",
    "status": "DRAFT",
    "total": "10000000.00",
    "customer": { "id": 1, "name": "ACME Corp" },
    "delivery_date": "2026-05-15",
    "items": [
        {
            "id": 1,
            "product": { "id": 1, "name": "Mouse" },
            "quantity": 10,
            "price": "15.00",
            "unit": { "id": 1, "name": "Piece" }
        },
        {
            "id": 2,
            "product": { "id": 2, "name": "Keyboard" },
            "quantity": 20,
            "price": "25.00",
            "unit": { "id": 2, "name": "Piece" }
        }
    ],
    "id": 6,
    "created_at": "2026-04-04T06:23:57.253807Z",
    "created_by": 9,
    "updated_at": "2026-04-04T06:23:57.253809Z",
    "updated_by": 9
}
```

## Create
**Endpoint:** `POST /api/sales/`
**Request Body:**
```json
{
    "customer_id": 1,
    "delivery_date": "2026-05-15",
    "items": [
        {
            "product_id": 1,
            "quantity": 10,
            "price": "15.00",
            "unit_id": 1
        },
        {
            "product_id": 2,
            "quantity": 20,
            "price": "25.00",
            "unit_id": 2
        }
    ]
}
```
**Response:**
```json
{
    "number": "SO-00001",
    "status": "DRAFT",
    "total": "10000000.00",
    "customer": { "id": 1, "name": "ACME Corp" },
    "delivery_date": "2026-05-15",
    "items": [
        {
            "id": 1,
            "product": { "id": 1, "name": "Mouse" },
            "quantity": 10,
            "price": "15.00",
            "unit": { "id": 1, "name": "Piece" }
        },
        {
            "id": 2,
            "product": { "id": 2, "name": "Keyboard" },
            "quantity": 20,
            "price": "25.00",
            "unit": { "id": 2, "name": "Piece" }
        }
    ],
    "id": 6,
    "created_at": "2026-04-04T06:23:57.253807Z",
    "created_by": 9,
    "updated_at": "2026-04-04T06:23:57.253809Z",
    "updated_by": 9
}
```

## Update (PUT and PATCH)
**Endpoint:** `PUT /api/sales/{id}`
**Request Body:**
PUT send all fields
PATCH send only changed fields
In items, if id is not provided, it will be created as new item.
If there are items that are not in the request, they will be deleted.
```json
{
    "customer_id": 1,
    "delivery_date": "2026-05-15",
    "items": [
        {
            "id": 1,
            "product_id": 1,
            "quantity": 10,
            "price": "15.00",
            "unit_id": 1
        },
        {
            "product_id": 2,
            "quantity": 20,
            "price": "25.00",
            "unit_id": 2
        }
    ]
}
```
**Response:**
PUT send all fields
PATCH send only changed fields
```json
{
    "number": "SO-00001",
    "status": "DRAFT",
    "total": "10000000.00",
    "customer": { "id": 1, "name": "ACME Corp" },
    "delivery_date": "2026-05-15",
    "items": [
        {
            "id": 1,
            "product": { "id": 1, "name": "Mouse" },
            "quantity": 10,
            "price": "15.00",
            "unit": { "id": 1, "name": "Piece" }
        },
        {
            "id": 2,
            "product": { "id": 2, "name": "Keyboard" },
            "quantity": 20,
            "price": "25.00",
            "unit": { "id": 2, "name": "Piece" }
        }
    ],
    "id": 6,
    "created_at": "2026-04-04T06:23:57.253807Z",
    "created_by": 9,
    "updated_at": "2026-04-04T06:23:57.253809Z",
    "updated_by": 9
}
```

## Delete
**Endpoint:** `DELETE /api/sales/{id}`
**Response:** `204 No Content`

## Confirm
**Endpoint:** `POST /api/sales/{id}/confirm/`
**Response:** `200 OK`

## Cancel
**Endpoint:** `POST /api/sales/{id}/cancel/`
**Response:** `200 OK`